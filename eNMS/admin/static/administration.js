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
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        }
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
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        }
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
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        }
        alertify.notify(`Query sent to openNMS.`, 'success', 5);
      },
    });
  }
}

/**
 * Query Netbox server.
 */
function queryNetbox() { // eslint-disable-line no-unused-vars
  if ($('#netbox_form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/query_netbox',
      data: $('#netbox_form').serialize(),
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        }
        alertify.notify(`Query sent to Netbox.`, 'success', 5);
      },
    });
  }
}

/**
 * Save geographical parameters.
 */
function saveGeographicalParameters() { // eslint-disable-line no-unused-vars
  if ($('#geographical-parameters-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/save_geographical_parameters',
      data: $('#geographical-parameters-form').serialize(),
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        }
        alertify.notify('Geographical parameters saved.', 'success', 5);
      },
    });
  }
}

/**
 * Save GoTTY parameters.
 */
function saveGottyParameters() { // eslint-disable-line no-unused-vars
  if ($('#gotty-parameters-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/save_gotty_parameters',
      data: $('#gotty-parameters-form').serialize(),
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        }
        alertify.notify('GoTTY parameters saved.', 'success', 5);
      },
    });
  }
}
