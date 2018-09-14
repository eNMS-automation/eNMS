/*
global
alertify: false
*/

/**
 * Create a new service.
 * @param {type} type - Type of service to create.
 */
function createService(type) { // eslint-disable-line no-unused-vars
  if ($(`#${type}-form`).parsley().validate() ) {
    const formData = new FormData($(`#${type}-form`)[0]);
    $.ajax({
      type: 'POST',
      url: `/services/create_service/${type}`,
      dataType: 'json',
      data: formData,
      contentType: false,
      cache: false,
      processData: false,
      async: false,
      success: function(service) {
        alertify.notify(`Service '${service.name}' created.`, 'success', 5);
      },
    });
  }
}
