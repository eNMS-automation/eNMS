var map = L.map('mapid').setView(
  [parameters.default_latitude, parameters.default_longitude],
  parameters.default_zoom_level
);
var osm_layer = L.tileLayer(layers['osm']);
map.addLayer(osm_layer);
var current_layer = osm_layer;
if (view == 'markercluster') {
  var markers = L.markerClusterGroup();
}

function switch_layer(layer){
  map.removeLayer(current_layer);
  current_layer = L.tileLayer(layers[layer]);
  map.addLayer(current_layer);
  $('.dropdown-submenu a.test').next('ul').toggle();
}

for (var i = 0; i < subtypes.length; i++) {
  window[`icon_${subtypes[i]}`] = L.icon({
    iconUrl: `static/images/default/${subtypes[i].toLowerCase()}.gif`,
    iconSize: [18, 12],
    iconAnchor: [9, 6],
    popupAnchor: [8, -5]
    });
  window[`icon_selected_${subtypes[i]}`] = L.icon({
  iconUrl: `static/images/selected/${subtypes[i].toLowerCase()}.gif`,
  iconSize: [18, 12],
  iconAnchor: [9, 6],
  popupAnchor: [8, -5]
  });
}

// Create a new vector type with getLatLng and setLatLng methods.
L.PolylineClusterable = L.Polyline.extend({
  _originalInitialize: L.Polyline.prototype.initialize,
  initialize: function (bounds, options) {
    this._originalInitialize(bounds, options);
    this._latlng = this.getBounds().getCenter();
  },
  getLatLng: function () { return this._latlng; },
  setLatLng: function () {}
});

for (var i = 0; i < nodes.length; i++) {
  var node = nodes[i]
  var marker = L.marker([
    node.latitude, 
    node.longitude
  ]);

  marker.node_id = node.id;
  marker.icon = window[`icon_${node.type}`];
  marker.selected_icon = window[`icon_selected_${node.type}`];
  marker.setIcon(marker.icon);
  markers_array.push(marker);

  marker.on("dblclick", function (e) {
    console.log(this.node_id);
    showObjectModal('node', this.node_id);
  });

  marker.on("click", function (e) {
    e.target.setIcon(e.target.selected_icon);
    selection.push(this.node_id);
    $("#nodes").val(selection);
  });

  marker.bindTooltip(node[labels.node], {
    permanent: false, 
  });

  if (view == 'leaflet') {
    marker.addTo(map);
  } else {
    markers.addLayer(marker);
    map.addLayer(markers);
  }
}

for (var i = 0; i < links.length; i++) {
  var link = links[i]
  var pointA = new L.LatLng(
    link.source_properties.latitude,
    link.source_properties.longitude
  );
  var pointB = new L.LatLng(
    link.destination_properties.latitude,
    link.destination_properties.longitude
  );
  var pointList = [pointA, pointB];
  var polyline = new L.PolylineClusterable(pointList, {
    color: link.color,
    weight: 3,
    opacity: 1,
    smoothFactor: 1
    });
  polyline_array.push(polyline);
  polyline.link_id = link.id;
  polyline.on("dblclick", function (e) {
    showObjectModal('link', this.link_id);
  });
  polyline.bindTooltip(link[labels.link], {
    permanent: false, 
    });
  if (view == 'leaflet') {
    polyline.addTo(map);
  } else {
    markers.addLayer(polyline);
  }
}

map.on("boxzoomend", function(e) {
  selection = [];
  for (var i = 0; i < markers_array.length; i++) {
    if (e.boxZoomBounds.contains(markers_array[i].getLatLng())) {
      markers_array[i].setIcon(markers_array[i].selected_icon);
      selection.push(markers_array[i].node_id);
      }
    }
  $("#nodes").val(selection);
});

map.on("contextmenu", function(e) {
  for (var i = 0; i < markers_array.length; i++) {
    markers_array[i].setIcon(markers_array[i].icon);
    }
  selection = [];
  $("#nodes").val(selection);
});

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
  $.ajax({
    type: "POST",
    url: `/objects/pool_objects/${this.value}`,
    dataType: "json",
    success: function(objects) {
      var nodes_id = objects.nodes.map(n => n.id);
      var links_id = objects.links.map(l => l.id);
      for (var i = 0; i < markers_array.length; i++) {
        if (nodes_id.includes(markers_array[i].node_id)) {
          markers_array[i].addTo(map);
        } else {
          markers_array[i].removeFrom(map);
        }
      }
      for (var i = 0; i < polyline_array.length; i++) {
        if (links_id.includes(polyline_array[i].link_id)) {
          polyline_array[i].addTo(map);
        } else {
          polyline_array[i].removeFrom(map);
        }
      }
      alertify.notify('Filter applied.', 'success', 5);
    }
  });
});