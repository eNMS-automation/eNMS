/*
global
alertify: false
fields: false
propertyTypes: false
types: false
services: false
servicesClasses: false
*/

(function() {
  for (let i = 0; i < servicesClasses.length; i++) {
    const cls = servicesClasses[i];
    $('#services').append(`<option value='${cls}'>${cls}</option>`);
  }
  buildServiceInstances();
})();

/**
 * Build select list of service instances.
 */
function buildServiceInstances() {
  $.ajax({
    type: 'POST',
    url: `/services/get_form/${$('#services').val()}`,
    success: function(result) {
      $('#service-instance').empty();
      $('#html-form').html(result.form);
      for (let i = 0; i < result.instances.length; i++) {
        const instance = result.instances[i];
        $('#service-instance').append(
          `<option value='${instance[0]}'>${instance[1]}</option>`
        );
      }
    },
  });
}

/**
 * Fill form with instance values.
 */
function fillInstanceForm() {
  $.ajax({
    type: 'POST',
    url: `/services/get_service/${$('#service-instance').val()}`,
    success: function(properties) {
      for (const [property, value] of Object.entries(properties)) {
        if (property.includes('bool')) {
          $(`#${property}`).prop('checked', value);
        } else if (property.includes('dict')) {
          $(`#${property}`).val(value ? JSON.stringify(value): '{}');
        } else {
          $(`#${property}`).val(value);
        }
      }
    alertify.notify(`Service '${properties.name}' displayed`, 'success', 5);
    },
  });
}

/**
 * Create or edit a service
 */
function saveService() { // eslint-disable-line no-unused-vars
  if ($('#form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: `/services/save_service/${$('#services').val()}`,
      dataType: 'json',
      data: $('#form').serialize(),
      success: function(result) {
        console.log(result);
      },
    });
  }
}

/**
 * Delete a service.
 * @param {id} id - Id of the service to delete.
 */
function deleteService(id) { // eslint-disable-line no-unused-vars

}


$('#services').change(function() {
  buildServiceInstances();
});

$('#service-instance').change(function() {
  fillInstanceForm();
});