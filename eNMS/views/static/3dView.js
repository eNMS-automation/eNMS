/*
global
enterPool: false
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
 * @param {nodeType} nodeType - Device or Pool.
 */
function createNode(node, nodeType) { // eslint-disable-line no-unused-vars
  const marker = WE.marker(
    [node.latitude, node.longitude],
    `static/images/3D/${nodeType == 'device' ? 'router' : 'site'}.gif`,
    15, 10
  ).addTo(map);
  marker.node_id = node.id;
  marker.on('click', function(e) {
    showTypeModal(nodeType, node.id);
  });
  marker.on('click', function(e) {
    if (nodeType == 'pool') {
      enterPool(this.node_id);
    } else {
      showTypeModal(nodeType, this.node_id);
    }
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
