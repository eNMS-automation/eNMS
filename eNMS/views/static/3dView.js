/*
global
call: false
layers: false
markersArray: true
partial: false
polylinesArray: true
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

/**
 * Create a device.
 * @param {device} device - Device.
 */
function createDevice(device) {
  const marker = WE.marker(
  [device.latitude, device.longitude],
  'static/images/3D/default/router.gif',
  15, 10
  ).addTo(map);
  marker.device_id = device.id;
  marker.on('click', function(e) {
    showTypeModal('device', device.id);
  });
  marker.on('contextmenu', function(e) {
    $('.global-menu,.link-menu').hide();
    $('.device-menu').show();
    selectedObject = device.id;
  });
  marker.on('mouseover', function(e) {
    $('#name-box').text(device.name);
    $('#name-box').show();
  });
  marker.on('mouseout', function(e) {
    $('#name-box').hide();
  });
  markersArray.push(marker);
}

/**
 * Create a link.
 * @param {link} link - Link.
 */
function createLink(link) {
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

/**
 * Delete all objects.
 */
function deleteAll() {
  for (let i = 0; i < markersArray.length; i++) {
    markersArray[i].removeFrom(map);
  }
  for (let i = 0; i < polylinesArray.length; i++) {
    try {
      polylinesArray[i].destroy();
    } catch (err) {
      // catch
    }
  }
  markersArray = [];
  polylinesArray = [];
}
