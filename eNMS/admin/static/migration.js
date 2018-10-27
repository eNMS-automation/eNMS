/*
global
alertify: false
call: false
*/

/**
 * Export services.
 */
function exportTopology() { // eslint-disable-line no-unused-vars
  call('/admin/export_services', function() {
    alertify.notify('Services successfully exported', 'success', 5);
  });
}
