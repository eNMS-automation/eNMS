var map = L.map('mapid').setView([parameters.default_latitude, parameters.default_longitude], parameters.default_zoom_level);
var osm_layer = L.tileLayer(layers['osm']);
map.addLayer(osm_layer);
var current_layer = osm_layer;
if (view == 'markercluster') {
  var markers = L.markerClusterGroup();
}

for (i = 0; i < subtypes.length; i++) {
  window[`icon_${subtypes[i]}`] = L.icon({
    iconUrl: `static/images/default/${subtypes[i]}.gif`,
    iconSize: [18, 12], // size of the icon
    iconAnchor: [9, 6], // point of the icon which will correspond to marker's location
    popupAnchor: [8, -5] // point from which the popup should open relative to the iconAnchor
    });
  window[`icon_selected_${subtypes[i]}`] = L.icon({
  iconUrl: 'static/images/selected/${subtypes[i]}.gif',
  iconSize: [18, 12], // size of the icon
  iconAnchor: [9, 6], // point of the icon which will correspond to marker's location
  popupAnchor: [8, -5] // point from which the popup should open relative to the iconAnchor
  });
}