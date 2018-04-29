function saveServer() {
  if ($('#form').parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/admin/save_tacacs_server",
      data: $('#form').serialize(),
      success: function() {
        alertify.notify(`Tacacs server saved`, 'success', 5);
      }
    });
  }
}