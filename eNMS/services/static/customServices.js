/*
global
alertify: false
fields: false
types: false
services: false
*/

(function() {
  for (let i = 0; i < servicesClasses.length; i++) {
    const cls = servicesClasses[i];
    $('#services').append(`<option value='${cls}'>${cls}</option>`);
  }
})();


/**
 * Delete a service.
 * @param {id} id - Id of the service to delete.
 */
function deleteService(id) { // eslint-disable-line no-unused-vars

}

$('#services').change(function() {
  $.ajax({
    type: 'POST',
    url: `/services/get_form/${$('#services').val()}`,
    success: function(result) {
      $('#html-form').html(result.form);
      for (let i = 0; i < result.instances.length; i++) {
        const instance = result.instances[i];
        $('#service-instance').append(`<option value='${instance}'>${instance}</option>`);
      } 
      console.log();
      alertify.notify('ok', 'success', 5);
    },
  });
  console.log();
});