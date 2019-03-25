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

const layers = {
  'osm': 'http://{s}.tile.osm.org/{z}/{x}/{y}.png',
  'gm': 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga',
  'nasa': 'http://tileserver.maptiler.com/nasa/{z}/{x}/{y}.jpg',
};

let selectedObject;
let markersArray = [];
let polylinesArray = [];
let viewMode = 'network';
let dimension = view.substring(0, 2);

const map = L.map('map').setView(
  [parameters.default_latitude, parameters.default_longitude],
  parameters.default_zoom_level
);
const options = {sky: true, atmosphere: true};
const earth = WE.map('earth', options);

const osmLayer = L.tileLayer(layers['osm']);
map.addLayer(osmLayer);
let layer2D = osmLayer;
let layer3D = WE.tileLayer(layers['gm']);
layer3D.addTo(earth);
let markers = L.markerClusterGroup();

if (view == '3D') {
  $('#map').css('visibility', 'hidden');
} else {
  $('#earth').css('visibility', 'hidden');
}

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
  $(`#btn-${view}`).hide();
  if (view == '2D') {
    $('#btn-2DC,#btn-3D').show();
  } else if (view == '2DC') {
    $('#btn-2D,#btn-3D').show();
  } else {
    $('#btn-2D,#btn-2DC').show();
  }
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

map.on('click', function(e) {
  selectedObject = null;
});

map.on('contextmenu', function() {
  if (!selectedObject) {
    $('.menu').hide();
    $(`.global-menu,.${viewMode}-menu`).show();
  }
});

$('.dropdown-submenu a.menu-submenu').on('click', function(e) {
  $(this).next('ul').toggle();
  e.stopPropagation();
  e.preventDefault();
});

$('body').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selectedObject);
    selectedObject = null;
  },
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/geographical_view.html');
  $('#pool-filter').change();
})();
