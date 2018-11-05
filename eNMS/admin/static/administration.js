/*
global
alertify: false
fCall: false
*/

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
 * Save Parameters.
 */
function saveParameters() { // eslint-disable-line no-unused-vars
  fCall('/admin/save_parameters', '#parameters-form', function() {
      alertify.notify('Notification parameters saved.', 'success', 5);
    }
  );
}

(function() {
  $('#doc-link').attr(
    'href',
    'https://enms.readthedocs.io/en/latest/security/access.html'
  );
})();
