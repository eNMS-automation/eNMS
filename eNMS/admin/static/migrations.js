/*
global
alertify: false
doc: false
fCall: false
*/

/**
 * Export all for migration.
 */
function migrationsExport() { // eslint-disable-line no-unused-vars
  alertify.notify('Export initiated.', 'success', 5);
  fCall('/objects/migration_export', '#import-export-form', function() {
    alertify.notify('Export successful.', 'success', 5);
  });
}

/**
 * Export all for migration.
 */
function migrationsImport() { // eslint-disable-line no-unused-vars
  alertify.notify('Import initiated.', 'success', 5);
  fCall('/objects/migration_import', '#import-export-form', function() {
    alertify.notify('Import successful.', 'success', 5);
  });
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
})();
