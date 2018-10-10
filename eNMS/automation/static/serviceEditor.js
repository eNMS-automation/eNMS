/*
global
alertify: false
propertyTypes: false
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
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        $('#service-instance').empty();
        $('#html-form').html(result.form);
        for (let i = 0; i < result.instances.length; i++) {
          const instance = result.instances[i];
          $('#service-instance').append(
            `<option value='${instance[0]}'>${instance[1]}</option>`
          );
        }
        if ($('#service-instance').val()) {
          fillInstanceForm();
        } else {
          $('#form').trigger('reset');
        }
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
    success: function(result) {
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        $('#name').empty();
        for (const [property, value] of Object.entries(result)) {
          const propertyType = propertyTypes[property] || 'str';
          if (propertyType.includes('bool')) {
            $(`#${property}`).prop('checked', value);
          } else if (propertyType.includes('dict')) {
            $(`#${property}`).val(value ? JSON.stringify(value): '{}');
          } else {
            $(`#${property}`).val(value);
          }
        }
        $('#devices').val(result.devices.map((n) => n.id));
        $('#pools').val(result.pools.map((p) => p.id));
        alertify.notify(`Service '${result.name}' displayed`, 'success', 5);
      }
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
      success: function(service) {
        if (!service) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          const isNew = $(`#service-instance option[value='${service.id}']`);
          if (0 == isNew.length) {
            $('#service-instance').append(
              `<option value='${service.id}'>${service.name}</option>`
            );
            alertify.notify(`Service '${service.name}' created.`, 'success', 5);
          } else {
            alertify.notify(`Service '${service.name}' updated.`, 'success', 5);
          }
        }
      },
    });
  }
}

$('#services').change(function() {
  buildServiceInstances();
});

$('#service-instance').change(function() {
  fillInstanceForm();
});
