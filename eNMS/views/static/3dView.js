var options = {sky: true, atmosphere: true};
var map = new WE.map('earth_div', options);
var current_layer = WE.tileLayer(layers['gm']);
current_layer.addTo(map);

function switchLayer(layer) {
  current_layer.removeFrom(map);
  current_layer = WE.tileLayer(layers[layer]);
  current_layer.addTo(map);
  $('.dropdown-submenu a.test').next('ul').toggle();
}

for (let i = 0; i < nodes.length; i++) { 
  var node = nodes[i]
  var marker = WE.marker(
  [node.latitude, node.longitude],
  'static/images/3D/default/router.gif', 
  15, 10
  ).addTo(map);
  marker.node_id = node.id;
  marker.on("dblclick", function (e) {
    showObjectModal('node', nodes[i].id);
  });
  markersArray.push(marker);
}

for (var i = 0; i < links.length; i++) {
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
  polylinesArray.push(polygonSD, polygonDS);
}

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
  $.ajax({
    type: "POST",
    url: `/objects/pool_objects/${this.value}`,
    dataType: "json",
    success: function(objects) {
      var nodes_id = objects.nodes.map(n => n.id);
      var links_id = objects.links.map(l => l.id);
      for (var i = 0; i < markersArray.length; i++) {
        if (nodes_id.includes(markersArray[i].node_id)) {
          markersArray[i].addTo(map);
        } else {
          markersArray[i].removeFrom(map);
        }
      }
      for (var i = 0; i < polylinesArray.length; i++) {
        try { polylinesArray[i].destroy(); }
        catch(err) {};
      }
      polylinesArray = [];
      for (var i = 0; i < objects.links.length; i++) {
        var link = objects.links[i];
        var source_latitude = link.source_properties.latitude;
        var source_longitude = link.source_properties.longitude;
        var destination_latitude = link.destination_properties.latitude;
        var destination_longitude = link.destination_properties.longitude;
        var color = link.color;
        var obj_id = link.id;
        console.log(source_latitude, destination_longitude, color, obj_id);
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
        polylinesArray.push(polygonSD, polygonDS);
      }
      alertify.notify('Filter applied.', 'success', 5);
    }
  });
});