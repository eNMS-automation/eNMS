/*
global
alertify: false
fCall: false
*/

/**
 * Export topology.
 */
function exportTopology() { // eslint-disable-line no-unused-vars
  call('/objects/export_topology', function() {});
}

/**
 * Import topology.
 * @param {objType} objType - Type of object.
 */
function importTopology(objType) { // eslint-disable-line no-unused-vars
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
      success: function(objects) {
        alertify.notify('Adding objects to the table...', 'success', 5);
        if (!objects) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          alertify.notify('Topology successfully imported.', 'success', 5);
        }
      },
    });
  }
}

/**
 * Export all for migration.
 */
function migrationImport() { // eslint-disable-line no-unused-vars
  fCall('/admin/migration_import', '#import-export-form', function() {
    alertify.notify('Import successful.', 'success', 5);
  });
}

(function() {
  $('#doc-link').attr(
    'href',
    'https://enms.readthedocs.io/en/latest/inventory/objects.html'
  );
})();
