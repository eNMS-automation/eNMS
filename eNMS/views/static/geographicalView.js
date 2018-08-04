var layers = {
  'osm': 'http://{s}.tile.osm.org/{z}/{x}/{y}.png',
  'gm': 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga',
  'nasa': 'http://tileserver.maptiler.com/nasa/{z}/{x}/{y}.jpg'
  };

var markers_array = [];
var polyline_array = [];
var selection = [];

function exportToGoogleEarth() {
  if ($("#google-earth-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/views/export_to_google_earth",
      dataType: "json",
      data: $("#google-earth-form").serialize(),
      success: function() {
        alertify.notify(`Project exported to Google Earth.`, 'success', 5);
      }
    });
    $("#google-earth").modal('hide');
  }
}

$('body').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function (invokedOn, selectedMenu) {
    var row = selectedMenu.text();
    action[row]();
  }
});