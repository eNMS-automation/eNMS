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

/**
 * Export project to Google Earth (creation of a .kmz file).
 */
function exportToGoogleEarth() {
  const url = '/views/export_to_google_earth';
  fCall(url, '#google-earth-form', function(result) {
    alertify.notify(`Project exported to Google Earth.`, 'success', 5);
    $('#google-earth').modal('hide');
  });
}

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

for (const [key, value] of Object.entries(subtype_sizes)) {
  window[`icon_${key}`] = L.icon({
    iconUrl: `static/images/2D/${key}.gif`,
    iconSize: value,
    iconAnchor: [9, 6],
    popupAnchor: [8, -5],
    });
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
  $(`#btn-${view}`).hide();
  if (view == '2D') {
    $('#btn-2DC,#btn-3D').show();
  } else if (view == '2DC') {
    $('#btn-2D,#btn-3D').show();
  } else {
    $('#btn-2D,#btn-2DC').show();
  }
  updateView();
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

/**
 * Create a node (device or pool).
 * @param {node} node - Device or Pool.
 * @param {nodeType} nodeType - Device or Pool.
 */
function createNode(node, nodeType) {
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
      enterPool(node.id);
    } else {
      showTypeModal(nodeType, node.id);
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
function createLink(link) {
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
function deleteAll() {
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
