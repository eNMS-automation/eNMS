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
const earth = WE.map('earth', options);


/**
 * Change the tile layer.
 * @param {layer} layer - tile layer.
 */
function switchLayer(layer) { // eslint-disable-line no-unused-vars
  layer3D.removeFrom(earth);
  layer3D = WE.tileLayer(layers[layer]);
  layer3D.addTo(earth);
  $('.dropdown-submenu a.menu-layer').next('ul').toggle();
}
