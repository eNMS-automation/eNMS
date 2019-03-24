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
const earth = WE.map('map', options);
let currentLayer = WE.tileLayer(layers['gm']);
currentLayer.addTo(earth);

/**
 * Change the tile layer.
 * @param {layer} layer - tile layer.
 */
function switchLayer(layer) { // eslint-disable-line no-unused-vars
  currentLayer.removeFrom(earth);
  currentLayer = WE.tileLayer(layers[layer]);
  currentLayer.addTo(earth);
  $('.dropdown-submenu a.menu-layer').next('ul').toggle();
}
