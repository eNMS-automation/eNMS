/*
global
alertify: false
links: false
markersArray: true
nodes: false
partial: false
polylinesArray: true
showModal: false
WE: false
*/

const options = {sky: true, atmosphere: true};
const map = new WE.map('earth_div', options);
const currentLayer = WE.tileLayer(layers['gm']);
currentLayer.addTo(map);

function switchLayer(layer) {
  currentLayer.removeFrom(map);
  currentLayer = WE.tileLayer(layers[layer]);
  currentLayer.addTo(map);
  $('.dropdown-submenu a.test').next('ul').toggle();
}

for (let i = 0; i < nodes.length; i++) { 
  const node = nodes[i]
  const marker = WE.marker(
  [node.latitude, node.longitude],
  'static/images/3D/default/router.gif', 
  15, 10
  ).addTo(map);
  marker.node_id = node.id;
  marker.on('dblclick', function(e) {
    showObjectModal('node', nodes[i].id);
  });
  markersArray.push(marker);
}

for (let i = 0; i < links.length; i++) {
  const link = links[i];
  const polygonSD = WE.polygon(
  [
    [link.source_properties.latitude, link.source_properties.longitude],
    [link.destination_properties.latitude, link.destination_properties.longitude],
    [link.source_properties.latitude, link.source_properties.longitude],
  ], {color: link.color, opacity: 20}
  ).addTo(map);
  const polygonDS = WE.polygon(
  [
    [link.destination_properties.latitude, link.destination_properties.longitude],
    [link.source_properties.latitude, link.source_properties.longitude],
    [link.destination_properties.latitude, link.destination_properties.longitude],
  ], {color: link.color, opacity: 20}
  ).addTo(map);

  polygonSD.link_id = polygonDS.link_id = link.id;
  polylinesArray.push(polygonSD, polygonDS);
}

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
  $.ajax({
    type: 'POST',
    url: `/objects/pool_objects/${this.value}`,
    dataType: 'json',
    success: function(objects) {
      const nodesId = objects.nodes.map(n => n.id);
      const linksId = objects.links.map(l => l.id);
      for (let i = 0; i < markersArray.length; i++) {
        if (nodesId.includes(markersArray[i].node_id)) {
          markersArray[i].addTo(map);
        } else {
          markersArray[i].removeFrom(map);
        }
      }
      for (let i = 0; i < polylinesArray.length; i++) {
        try { polylinesArray[i].destroy(); }
        catch(err) {};
      }
      polylinesArray = [];
      for (let i = 0; i < objects.links.length; i++) {
        const link = objects.links[i];
        const source_latitude = link.source_properties.latitude;
        const source_longitude = link.source_properties.longitude;
        const destination_latitude = link.destination_properties.latitude;
        const destination_longitude = link.destination_properties.longitude;
        const color = link.color;
        const objId = link.id;
        console.log(source_latitude, destination_longitude, color, objId);
        const polygonSD = WE.polygon(
        [
          [source_latitude, source_longitude],
          [destination_latitude, destination_longitude],
          [source_latitude, source_longitude]
        ], {color: color, opacity: 20}
        ).addTo(map);
        const polygonDS = WE.polygon(
        [
          [destination_latitude, destination_longitude],
          [source_latitude, source_longitude],
          [destination_latitude, destination_longitude]
        ], {color: color, opacity: 20}
        ).addTo(map);
        polygonSD.link_id = polygonDS.link_id = objId;
        polylinesArray.push(polygonSD, polygonDS);
      }
      alertify.notify('Filter applied.', 'success', 5);
    },
  });
});

const action = {
  'Parameters': partial(showModal, 'filters'),
  'Export to Google Earth': partial(showModal, 'google-earth'),
  'Add new task': partial(showModal, 'scheduling'),
  'Open Street Map': partial(switchLayer, 'osm'),
  'Google Maps': partial(switchLayer, 'gm'),
  'NASA': partial(switchLayer, 'nasa')
}

$('body').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row]();
  }
});