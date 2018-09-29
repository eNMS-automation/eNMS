/*
global
alertify: false
*/

/**
 * Save geographical parameters.
 */
function saveGeographicalParameters() { // eslint-disable-line no-unused-vars
  if ($('#geographical-parameters-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/save_geographical_parameters',
      data: $('#geographical-parameters-form').serialize(),
      success: function() {
        alertify.notify('Geographical parameters saved.', 'success', 5);
      },
    });
  }
}

/**
 * Save GoTTY parameters.
 */
function saveGottyParameters() { // eslint-disable-line no-unused-vars
  if ($('#gotty-parameters-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/save_gotty_parameters',
      data: $('#gotty-parameters-form').serialize(),
      success: function() {
        alertify.notify('GoTTY parameters saved.', 'success', 5);
      },
    });
  }
}
