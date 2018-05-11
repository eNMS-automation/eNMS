function saveTacacsServer() {
  if ($('#tacacs_form').parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/admin/save_tacacs_server",
      data: $('#tacacs_form').serialize(),
      success: function() {
        alertify.notify(`Tacacs server saved`, 'success', 5);
      }
    });
  }
}

function saveSyslogServer() {
  if ($('#syslog_form').parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/admin/save_syslog_server",
      data: $('#syslog_form').serialize(),
      success: function() {
        alertify.notify(`Syslog server saved`, 'success', 5);
      }
    });
  }
}