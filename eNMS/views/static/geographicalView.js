/*
global
alertify: false
doc: false
fCall: false
*/

const layers = { // eslint-disable-line no-unused-vars
  'osm': 'http://{s}.tile.osm.org/{z}/{x}/{y}.png',
  'gm': 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga',
  'nasa': 'http://tileserver.maptiler.com/nasa/{z}/{x}/{y}.jpg',
};

let markersArray = []; // eslint-disable-line no-unused-vars
let polylinesArray = []; // eslint-disable-line no-unused-vars
let selection = []; // eslint-disable-line no-unused-vars

/**
 * Export project to Google Earth (creation of a .kmz file).
 */
function exportToGoogleEarth() { // eslint-disable-line no-unused-vars
  const url = '/views/export_to_google_earth';
  fCall(url, '#google-earth-form', function(result) {
    alertify.notify(`Project exported to Google Earth.`, 'success', 5);
    $('#google-earth').modal('hide');
  });
}

$('.dropdown-submenu a.menu-submenu').on('click', function(e) {
  $(this).next('ul').toggle();
  e.stopPropagation();
  e.preventDefault();
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/geographical_view.html');
})();
