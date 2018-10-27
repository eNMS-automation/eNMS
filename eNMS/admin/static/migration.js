/*
global
alertify: false
call: false
*/

/**
 * Export services.
 */
function export() { // eslint-disable-line no-unused-vars
  call('/admin/export', function() {
    alertify.notify('Services successfully exported', 'success', 5);
  });
}
