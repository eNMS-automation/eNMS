/*
global
alertify: false
*/

/**
 * Save geographical parameters.
 */
function saveGeographicalParameters() { // eslint-disable-line no-unused-vars
  if ($('#geographical_parameters_form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/save_geographical_parameters',
      data: $('#geographical_parameters_form').serialize(),
      success: function() {
        alertify.notify(`Geographical parameters saved.`, 'success', 5);
      },
    });
  }
}
