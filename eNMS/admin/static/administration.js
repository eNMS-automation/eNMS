/*
global
alertify: false
fCall: false
*/

/**
 * Save Tacacs server.
 */
function saveTacacsServer() { // eslint-disable-line no-unused-vars
  fCall('/admin/save_tacacs_server', '#tacacs_form', function() {
    alertify.notify(`Tacacs server saved.`, 'success', 5);
  });
}

/**
 * Save Syslog server.
 */
function saveSyslogServer() { // eslint-disable-line no-unused-vars
  fCall('/admin/save_syslog_server', '#syslog_form', function() {
    alertify.notify('Syslog server saved.', 'success', 5);
  });
}

/**
 * Query openNMS server.
 */
function queryOpenNMS() { // eslint-disable-line no-unused-vars
  fCall('/admin/query_opennms', '#opennms_form', function() {
    alertify.notify('Topology imported from OpenNMS.', 'success', 5);
  });
}

/**
 * Query Netbox server.
 */
function queryNetbox() { // eslint-disable-line no-unused-vars
  fCall('/admin/query_netbox', '#netbox_form', function() {
    alertify.notify('Topology imported from Netbox.', 'success', 5);
  });
}

/**
 * Save geographical parameters.
 */
function saveGeographicalParameters() { // eslint-disable-line no-unused-vars
  fCall(
    '/admin/save_geographical_parameters',
    '#geographical-parameters-form',
    function() {
      alertify.notify('Geographical parameters saved.', 'success', 5);
    }
  );
}

/**
 * Save GoTTY parameters.
 */
function saveGottyParameters() { // eslint-disable-line no-unused-vars
  fCall('/admin/save_gotty_parameters', '#gotty-parameters-form', function() {
    alertify.notify('GoTTY parameters saved.', 'success', 5);
  });
}

(function() {
  $('#doc-link').attr(
    'href',
    'https://enms.readthedocs.io/en/latest/security/access.html'
  );
})();
