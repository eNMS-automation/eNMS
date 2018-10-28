/*
global
alertify: false
fCall: false
*/



/**
 * Save GoTTY parameters.
 */
function saveGottyParameters() { // eslint-disable-line no-unused-vars
  fCall('/admin/save_gotty_parameters', '#gotty-parameters-form', function() {
    alertify.notify('GoTTY parameters saved.', 'success', 5);
  });
}

/**
 * Export all for migration.
 */
function migrationExport() { // eslint-disable-line no-unused-vars
  fCall('/admin/migration_export', '#import-export-form', function() {
    alertify.notify('Export successful.', 'success', 5);
  });
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
    'https://enms.readthedocs.io/en/latest/security/access.html'
  );
})();
