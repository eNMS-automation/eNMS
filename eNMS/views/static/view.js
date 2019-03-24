/*
global
enterPool: false
L: false
layers: false
link_colors: false
markersArray: true
parameters: false
polylinesArray: true
showTypeModal: false
subtype_sizes: false
view: false
WE: false
*/

const layers = { // eslint-disable-line no-unused-vars
  'osm': 'http://{s}.tile.osm.org/{z}/{x}/{y}.png',
  'gm': 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga',
  'nasa': 'http://tileserver.maptiler.com/nasa/{z}/{x}/{y}.jpg',
};

let selectedObject; // eslint-disable-line no-unused-vars
let markersArray = []; // eslint-disable-line no-unused-vars
let polylinesArray = []; // eslint-disable-line no-unused-vars

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

let markers;
let dimension = '2D';
let viewMode = 'network';

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
if (view == '2DC') {
  markers = L.markerClusterGroup();
  map.addLayer(markers);
}

$('#earth').css('visibility', 'hidden');

/**
 * Switch dimension.
 * @param {dimension} dimension - Dimension.
 */
function switchDimension(dimension) {
  $('#map,#earth').css('visibility', 'visible');
  $('.flip-container').toggleClass('hover');
  setTimeout(function() {
    if (dimension == '3D') {
      $('#map').css('visibility', 'hidden');
    } else {
      $('#earth').css('visibility', 'hidden');
    }
  }, 1600);
}

/**
 * Change the tile layer.
 * @param {layer} layer - tile layer.
 */
function switchLayer(layer) { // eslint-disable-line no-unused-vars
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

/**
 * Create a node (device or pool).
 * @param {node} node - Device or Pool.
 * @param {nodeType} nodeType - Device or Pool.
 */
function createNode(node, nodeType) { // eslint-disable-line no-unused-vars
  if (view == '2D' || view == '2DC') {
    marker = L.marker([node.latitude, node.longitude]);
    if (nodeType === 'device') {
      marker.icon = window[`icon_${node.subtype}`] || routerIcon;
    } else {
      marker.icon = window['icon_site'];
    }
    marker.setIcon(marker.icon);
    marker.bindTooltip(node['name'], {permanent: false});
  } else {
    marker = WE.marker(
      [node.latitude, node.longitude],
      `static/images/3D/${nodeType == 'device' ? 'router' : 'site'}.gif`,
      15, 10
    ).addTo(earth);
    marker.on('mouseover', function(e) {
      $('#name-box').text(node.name);
      $('#name-box').show();
    });
    marker.on('mouseout', function(e) {
      $('#name-box').hide();
    });
  }
  marker.node_id = node.id;
  markersArray.push(marker);
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
  if (view == '2D') {
    marker.addTo(map);
  } else if (view == '2DC') {
    markers.addLayer(marker);
  }
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
  if (view == '2D' || view == '2DC') {
    let pointA = new L.LatLng(sourceLatitude, sourceLongitude);
    let pointB = new L.LatLng(destinationLatitude, destinationLongitude);
    const pointList = [pointA, pointB];
    const polyline = new L.PolylineClusterable(pointList, {
      color: link_colors[link.subtype],
      weight: 3,
      opacity: 1,
      smoothFactor: 1,
    });
    polylinesArray.push(polyline);
    polyline.link_id = link.id;
    polyline.on('click', function(e) {
      showTypeModal('link', this.link_id);
    });
    polyline.on('contextmenu', function(e) {
      $('.menu').hide();
      $('.rc-link-menu').show();
      selectedObject = this.link_id; // eslint-disable-line no-undef
    });
    polyline.bindTooltip(link['name'], {
      permanent: false,
    });
    if (view == '2D') {
      polyline.addTo(map);
    } else {
      markers.addLayer(polyline);
    }
  } else {
    const color = link.color;
    const polygonSD = WE.polygon(
    [
      [sourceLatitude, sourceLongitude],
      [destinationLatitude, destinationLongitude],
      [sourceLatitude, sourceLongitude],
    ], {color: color, opacity: 20}
    ).addTo(earth);
    const polygonDS = WE.polygon(
    [
      [destinationLatitude, destinationLongitude],
      [sourceLatitude, sourceLongitude],
      [destinationLatitude, destinationLongitude],
    ], {color: color, opacity: 20}
    ).addTo(earth);
    polygonSD.link_id = polygonDS.link_id = link.id;
    polylinesArray.push(polygonSD, polygonDS);
  }
}

/**
 * Delete all devices and links on the map.
 */
function deleteAll() { // eslint-disable-line no-unused-vars
  for (let i = 0; i < markersArray.length; i++) {
    if (view == '2D') {
      markersArray[i].removeFrom(map);
    } else if (view == '3D') {
      markersArray[i].removeFrom(earth);
    } else {
      markers.removeLayer(markersArray[i]);
    }
  }
  for (let i = 0; i < polylinesArray.length; i++) {
    if (view == '2D') {
      polylinesArray[i].removeFrom(map);
    } else if (view == '2DC') {
      markers.removeLayer(polylinesArray[i]);
    } else {
      try {
        polylinesArray[i].destroy();
      } catch (err) {
        // catch
      }
    }
  }
  markersArray = [];
  polylinesArray = [];
}

/**
 * Display pools.
 */
function displayPools() { // eslint-disable-line no-unused-vars
  viewMode = 'site';
  deleteAll();
  $('#map').css('visibility', 'visible');
  call('/get_all/pool', function(pools) {
    for (let i = 0; i < pools.length; i++) {
      if (pools[i].longitude) {
        createNode(pools[i], 'pool');
      }
    }
  });
  $('.menu,#pool-filter,#network').hide();
  $('.geo-menu,.rc-pool-menu').show();
  alertify.notify('Site view');
}

/**
 * Display network.
 */
function displayNetwork() { // eslint-disable-line no-unused-vars
  viewMode = 'network';
  $('#pool-filter').change();
  $('#map').css('visibility', 'visible');
  $('.menu,#network').hide();
  $('.geo-menu,#pool-filter').show();
  alertify.notify('Network view.');
}

/**
 * Enter pool.
 * @param {poolId} poolId - Pool ID.
 */
function enterPool(poolId) { // eslint-disable-line no-unused-vars
  viewMode = 'insite';
  $('#map').css('visibility', 'hidden');
  $('.menu').hide();
  $('#network,.insite-menu,rc-device-menu,rc-link-menu').show();
  call(`/inventory/pool_objects/${poolId}`, function(objects) {
    alertify.notify('Loading the view...', 3);
    displayPool(objects.devices, objects.links);
  });
}

$('#pool-filter').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    deleteAll();
    objects.devices.map((d) => createNode(d, 'device'));
    objects.links.map(createLink);
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
  'Display pools': displayPools,
  'Display network': displayNetwork,
  'Enter pool': enterPool,
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

$('#network').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selected);
  },
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/geographical_view.html');
  switchDimension();
  $('#pool-filter').change();
})();
