/*
global
alertify: false
call: false
*/

/**
 * Export all for migration.
 */
function migrationExport() { // eslint-disable-line no-unused-vars
  call('/admin/export', function() {
    alertify.notify('Export successful.', 'success', 5);
  });
}
