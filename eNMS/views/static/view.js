/*
global
enterPool: false
L: false
link_colors: false
parameters: false
showTypeModal: false
subtype_sizes: false
view: false
WE: false
*/

/**
 * Switch dimension.
 * @param {dimension} dimension - Dimension.
 */
function switchView(newView) {
  $('#map,#earth').css('visibility', 'visible');
  deleteAll();
  view = newView;
  newDimension = newView.substring(0, 2);
  console.log(dimension != newDimension);
  if (dimension != newDimension) {
    $('.flip-container').toggleClass('hover');
    setTimeout(function() {
      if (newDimension == '3D') {
        $('#map').css('visibility', 'hidden');
      } else {
        $('#earth').css('visibility', 'hidden');
      }
    }, 1600);
  }
  dimension = newDimension;
  $('#pool-filter').change();
}

/**
 * Change the tile layer.
 * @param {layer} layer - tile layer.
 */
function switchLayer(layer) {
  if (view == '2D' || view == '2DC') {
    map.removeLayer(layer2D);
    layer2D = L.tileLayer(layers[layer]);
    map.addLayer(layer2D);
  } else {
    layer3D.removeFrom(earth);
    layer3D = WE.tileLayer(layers[layer]);
    layer3D.addTo(earth);
  }
  $('.dropdown-submenu a.menu-layer').next('ul').toggle();
}

for (const [key, value] of Object.entries(subtype_sizes)) {
  window[`icon_${key}`] = L.icon({
    iconUrl: `static/images/2D/${key}.gif`,
    iconSize: value,
    iconAnchor: [9, 6],
    popupAnchor: [8, -5],
    });
}

L.PolylineClusterable = L.Polyline.extend({
  _originalInitialize: L.Polyline.prototype.initialize,
  initialize: function(bounds, options) {
    this._originalInitialize(bounds, options);
    this._latlng = this.getBounds().getCenter();
  },
  getLatLng: function() {
    return this._latlng;
  },
  setLatLng: function() {
  },
});

const routerIcon = window['icon_router'];

function updateView() {
  $('#pool-filter').change();
}

$('#pool-filter').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    deleteAll();
    objects.devices.map((d) => createNode(d, 'device'));
    objects.links.map(createLink);
    if (view == '2DC') {
      map.addLayer(markers);
    }
  });
});

const action = {
  'Export to Google Earth': partial(showModal, 'google-earth'),
  'Open Street Map': partial(switchLayer, 'osm'),
  'Google Maps': partial(switchLayer, 'gm'),
  'NASA': partial(switchLayer, 'nasa'),
  'Device properties': (d) => showTypeModal('device', d),
  'Link properties': (l) => showTypeModal('link', l),
  'Pool properties': (p) => showTypeModal('pool', p),
  'Connect': connectionParametersModal,
  'Automation': deviceAutomationModal,
};

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/geographical_view.html');
  updateView();
})();
