function exportToGoogleEarth() {
  if ($("#google-earth-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/views/export_to_google_earth",
      dataType: "json",
      data: $("#google-earth-form").serialize(),
      success: function() {
        alertify.notify(`Project exported to Google Earth`, 'success', 5);
      }
    });
    $("#google-earth").modal('hide');
  }
}