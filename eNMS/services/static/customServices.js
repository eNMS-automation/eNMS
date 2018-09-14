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
  $.ajax({
    type: 'POST',
    url: `/services/delete/${id}`,
    success: function(serviceName) {
      table.row($(`#${id}`)).remove().draw(false);
      const message = `Service '${serviceName}' successfully deleted.`;
      alertify.notify(message, 'error', 5);
    },
  });
}

$('#services').change(function() {
  console.log($('#services').val());
});