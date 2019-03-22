/*
global
layers: false
markersArray: true
polylinesArray: true
showTypeModal: false
WE: false
*/

const options = {sky: true, atmosphere: true};
const map = WE.map('map', options);
let currentLayer = WE.tileLayer(layers['gm']);
currentLayer.addTo(map);

/**
 * Change the tile layer.
 * @param {layer} layer - tile layer.
 */
function switchLayer(layer) { // eslint-disable-line no-unused-vars
  currentLayer.removeFrom(map);
  currentLayer = WE.tileLayer(layers[layer]);
  currentLayer.addTo(map);
  $('.dropdown-submenu a.menu-layer').next('ul').toggle();
}

/**
 * Create a device or a pool.
 * @param {node} node - Device or pool.
 */
function createNode(node, nodeType) { // eslint-disable-line no-unused-vars
  const marker = WE.marker(
    [node.latitude, node.longitude],
    `static/images/3D/default/${nodeType == 'device' ? 'router' : 'site'}.gif`,
    15, 10
  ).addTo(map);
  marker.node_id = node.id;
  marker.on('click', function(e) {
    showTypeModal(nodeType, node.id);
  });
  marker.on('contextmenu', function(e) {
    $('.menu').hide();
    $(`.rc-${nodeType}-menu`).show();
    selectedObject = node.id; // eslint-disable-line no-undef
  });
  marker.on('mouseover', function(e) {
    $('#name-box').text(node.name);
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
function createLink(link) { // eslint-disable-line no-unused-vars
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
function deleteAll() { // eslint-disable-line no-unused-vars
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
