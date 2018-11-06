/*
global
alertify: false
call: false
layers: false
links: false
markersArray: true
devices: false
partial: false
polylinesArray: true
selection: true
showModal: false
showTypeModal: false
WE: false
*/

const options = {sky: true, atmosphere: true};
const map = WE.map('earth_div', options);
let currentLayer = WE.tileLayer(layers['gm']);
currentLayer.addTo(map);

/**
 * Change the tile layer.
 * @param {layer} layer - tile layer.
 */
function switchLayer(layer) {
  currentLayer.removeFrom(map);
  currentLayer = WE.tileLayer(layers[layer]);
  currentLayer.addTo(map);
  $('.dropdown-submenu a.menu-layer').next('ul').toggle();
}

for (let i = 0; i < devices.length; i++) {
  const device = devices[i];
  const marker = WE.marker(
  [device.latitude, device.longitude],
  'static/images/3D/default/router.gif',
  15, 10
  ).addTo(map);
  marker.device_id = device.id;
  marker.on('click', function(e) {
    /*
      $(e.target.element.children[0]).css(
      'background-image',
      'url("static/images/3D/selection/router.gif")'
      );
      selection.push(devices[i].id);
      $('#devices').val(selection);
    */
    showTypeModal('device', devices[i].id);
  });
  marker.on('mouseover', function(e) {
    $('#name-box').text(devices[i].name);
    $('#name-box').show();
  });
  marker.on('mouseout', function(e) {
    $('#name-box').hide();
  });
  markersArray.push(marker);
}

for (let i = 0; i < links.length; i++) {
  const link = links[i];
  const sourceLatitude = link.source.latitude;
  const sourceLongitude = link.source.longitude;
  const destinationLatitude = link.destination.latitude;
  const destinationLongitude = link.destination.longitude;
  const color = link.color;
  const polygonSD = WE.polygon(
  [
    [sourceLatitude, sourceLongitude],
    [destinationLatitude, destinationLongitude],
    [sourceLatitude, sourceLongitude],
  ], {color: color, opacity: 20}
  ).addTo(map);
  const polygonDS = WE.polygon(
  [
    [destinationLatitude, destinationLongitude],
    [sourceLatitude, sourceLongitude],
    [destinationLatitude, destinationLongitude],
  ], {color: color, opacity: 20}
  ).addTo(map);
  polygonSD.link_id = polygonDS.link_id = link.id;
  polylinesArray.push(polygonSD, polygonDS);
}

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
  call(`/objects/pool_objects/${this.value}`, function(objects) {
    const devicesId = objects.devices.map((n) => n.id);
    for (let i = 0; i < markersArray.length; i++) {
      if (devicesId.includes(markersArray[i].device_id)) {
        markersArray[i].addTo(map);
      } else {
        markersArray[i].removeFrom(map);
      }
    }
    for (let i = 0; i < polylinesArray.length; i++) {
      try {
        polylinesArray[i].destroy();
      } catch (err) {
        // ignore
      }
    }
    polylinesArray = [];
    for (let i = 0; i < objects.links.length; i++) {
      const link = objects.links[i];
      const sourceLatitude = link.source.latitude;
      const sourceLongitude = link.source.longitude;
      const destinationLatitude = link.destination.latitude;
      const destinationLongitude = link.destination.longitude;
      const color = link.color;
      const objId = link.id;
      const polygonSD = WE.polygon(
      [
        [sourceLatitude, sourceLongitude],
        [destinationLatitude, destinationLongitude],
        [sourceLatitude, sourceLongitude],
      ], {color: color, opacity: 20}
      ).addTo(map);
      const polygonDS = WE.polygon(
      [
        [destinationLatitude, destinationLongitude],
        [sourceLatitude, sourceLongitude],
        [destinationLatitude, destinationLongitude],
      ], {color: color, opacity: 20}
      ).addTo(map);
      polygonSD.link_id = polygonDS.link_id = objId;
      polylinesArray.push(polygonSD, polygonDS);
    }
    alertify.notify('Filter applied.', 'success', 5);
  });
});

/**
 * Unselect all devices.
 */
function unselectAll() {
  for (let i = 0; i < markersArray.length; i++) {
    $(markersArray[i].element.children[0]).css(
      'background-image',
      'url("static/images/3D/default/router.gif")'
    );
  }
  selection = [];
  $('#devices').val(selection);
}

map.on('click', function(e) {
  unselectAll();
});


const action = {
  'Parameters': partial(showModal, 'filters'),
  'Export to Google Earth': partial(showModal, 'google-earth'),
  'Add new task': partial(showModal, 'scheduling'),
  'Open Street Map': partial(switchLayer, 'osm'),
  'Google Maps': partial(switchLayer, 'gm'),
  'NASA': partial(switchLayer, 'nasa'),
};

$('body').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row]();
  },
});
