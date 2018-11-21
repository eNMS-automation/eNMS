/*
global
alertify: false
doc: false
fCall: false
parameters: false
*/

/**
 * Save Parameters.
 */
function saveParameters() { // eslint-disable-line no-unused-vars
  fCall('/admin/save_parameters', '#parameters-form', function() {
      alertify.notify('Parameters saved.', 'success', 5);
    }
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  $('#default_view').val(parameters.default_view);
  if (parameters.pool) {
    $('#pool').val(parameters.pool.id);
  }
})();
