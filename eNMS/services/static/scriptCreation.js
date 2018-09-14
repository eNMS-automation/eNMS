/*
global
alertify: false
*/

/**
 * Create a new script.
 * @param {type} type - Type of script to create.
 */
function createScript(type) { // eslint-disable-line no-unused-vars
  if ($(`#${type}-form`).parsley().validate() ) {
    const formData = new FormData($(`#${type}-form`)[0]);
    $.ajax({
      type: 'POST',
      url: `/scripts/create_script/${type}`,
      dataType: 'json',
      data: formData,
      contentType: false,
      cache: false,
      processData: false,
      async: false,
      success: function(script) {
        alertify.notify(`Script '${script.name}' created.`, 'success', 5);
      },
    });
  }
}
