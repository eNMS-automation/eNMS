var options = {sky: true, atmosphere: true};
var map = new WE.map('earth_div', options);
var current_layer = WE.tileLayer(layers['gm']);
current_layer.addTo(map);

function switch_layer(layer) {
  current_layer.removeFrom(map);
  current_layer = WE.tileLayer(layers[layer]);
  current_layer.addTo(map);
}

for (i = 0; i < nodes.length; i++) { 
  var node = nodes[i]
  var marker = WE.marker(
  [node.latitude, node.longitude],
  'static/images/3D/default/router.gif', 
  15, 10
  ).addTo(map);

  marker.on("dblclick", function (e) {
    showObjectModal('node', '${node.id}');
  });

  marker.node_id = node.id;
  markers_array.push(marker);
}

for (i = 0; i < links.length; i++) {
  var link = links[i] 
  var polygonSD = WE.polygon(
  [
    [link.source_properties.latitude, link.source_properties.longitude],
    [link.destination_properties.latitude, link.destination_properties.longitude],
    [link.source_properties.latitude, link.source_properties.longitude]
  ], {color: link.color, opacity: 20}
  ).addTo(map);
  var polygonDS = WE.polygon(
  [
    [link.destination_properties.latitude, link.destination_properties.longitude],
    [link.source_properties.latitude, link.source_properties.longitude],
    [link.destination_properties.latitude, link.destination_properties.longitude]
  ], {color: link.color, opacity: 20}
  ).addTo(map);

  polygonSD.link_id = polygonDS.link_id = link.id;
  polyline_array.push(polygonSD, polygonDS);
}

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
  var filterName = this.value;
  $.ajax({
    type: "POST",
    url: `/objects/pool_objects/${this.value}`,
    dataType: "json",
    success: function(objects){
      for (i = 0; i < markers_array.length; i++) {
        if (objects['nodes'].includes(markers_array[i].node_id)) {
          markers_array[i].addTo(map);
        } else {
          markers_array[i].removeFrom(map);
        }
      }
      for (i = 0; i < polyline_array.length; i++) {
        try { polyline_array[i].destroy(); }
        catch(err) {};
      }
      polyline_array = [];
      for (i = 0; i < objects['links'][1].length; i++) {
        var source_latitude = objects['links'][1][i][0],
            source_longitude = objects['links'][1][i][1],
            destination_latitude = objects['links'][1][i][2],
            destination_longitude = objects['links'][1][i][3],
            color = objects['links'][1][i][4],
            obj_id = objects['links'][0][i];
        var polygonSD = WE.polygon(
        [
          [source_latitude, source_longitude],
          [destination_latitude, destination_longitude],
          [source_latitude, source_longitude]
        ], {color: color, opacity: 20}
        ).addTo(map);
        var polygonDS = WE.polygon(
        [
          [destination_latitude, destination_longitude],
          [source_latitude, source_longitude],
          [destination_latitude, destination_longitude]
        ], {color: color, opacity: 20}
        ).addTo(map);
        polygonSD.link_id = polygonDS.link_id = obj_id;
        polyline_array.push(polygonSD, polygonDS);
      }
      alertify.notify(`Filter '${filterName}' applied`, 'success', 5);
    }
  });
});