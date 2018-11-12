/*
global
alertify: false
call: false
doc: false
fCall: false
*/

document.getElementById('file').onchange = function() {
  importTopology('Device');
};

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
 * Export topology.
 */
function exportTopology() { // eslint-disable-line no-unused-vars
  call('/objects/export_topology', function() {
    alertify.notify('Topology successfully exported.', 'success', 5);
  });
}

/**
 * Import topology.
 */
function importTopology() { // eslint-disable-line no-unused-vars
  alertify.notify('Topology import: starting...', 'success', 5);
  if ($('#import-form').parsley().validate() ) {
    const formData = new FormData($('#import-form')[0]);
    $.ajax({
      type: 'POST',
      url: '/objects/import_topology',
      dataType: 'json',
      data: formData,
      contentType: false,
      processData: false,
      async: false,
      success: function(result) {
        alertify.notify(result, 'success', 5);
      },
    });
  }
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
})();
