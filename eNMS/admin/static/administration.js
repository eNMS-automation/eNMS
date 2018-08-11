/*
global
alertify: false
*/

/**
 * Save Tacacs server.
 */
function saveTacacsServer() { // eslint-disable-line no-unused-vars
  if ($('#tacacs_form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/save_tacacs_server',
      data: $('#tacacs_form').serialize(),
      success: function() {
        alertify.notify(`Tacacs server saved.`, 'success', 5);
      },
    });
  }
}

/**
 * Save Syslog server.
 */
function saveSyslogServer() { // eslint-disable-line no-unused-vars
  if ($('#syslog_form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/save_syslog_server',
      data: $('#syslog_form').serialize(),
      success: function() {
        alertify.notify(`Syslog server saved.`, 'success', 5);
      },
    });
  }
}

/**
 * Query openNMS server.
 */
function queryOpenNMS() { // eslint-disable-line no-unused-vars
  if ($('#opennms_form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/query_opennms',
      data: $('#opennms_form').serialize(),
      success: function() {
        alertify.notify(`Query sent to openNMS.`, 'success', 5);
      },
    });
  }
}
