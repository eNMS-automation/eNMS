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
 * Initialize the open wizard (Service Editor).
 */
function openWizard() { // eslint-disable-line no-unused-vars
  $('#wizard').smartWizard({
    onFinish: saveService,
    enableFinishButton: true,
  });
  $('.buttonNext').addClass('btn btn-success');
  $('.buttonPrevious').addClass('btn btn-primary');
  $('.buttonFinish').addClass('btn btn-default');
}

/**
 * Build select list of service instances.
 */
function buildServiceInstances(type) {
  $.ajax({
    type: 'POST',
    url: `/automation/get_form/${type || $('#services').val()}`,
    success: function(result) {
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        $('#html-form').html(result.form);
      }
    },
  });
}

/**
 * Edit a service.
 */
function editService(type, id) {
  buildServiceInstances(type);
  $.ajax({
    type: 'POST',
    url: `/automation/get_service/${id}`,
    success: function(result) {
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        
        for (const [property, value] of Object.entries(result)) {
          const propertyType = propertyTypes[property] || 'str';
          if (propertyType.includes('bool')) {
            $(`#${property}`).prop('checked', value);
          } else if (propertyType.includes('dict')) {
            $(`#${property}`).val(value ? JSON.stringify(value): '{}');
          } else {
            console.log(property, value);
            console.log($(`#${property}`));
            $(`#${property}`).val(value);
            console.log($(`#${property}`).val());
          }
        }
        $('#devices').val(result.devices.map((n) => n.id));
        $('#pools').val(result.pools.map((p) => p.id));
        showModal('service-editor');
      }
    },
  });
}

/**
 * Save a service.
 */
function saveService() { // eslint-disable-line no-unused-vars
  if ($('#service-editor-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: `/automation/save_service/${$('#services').val()}`,
      dataType: 'json',
      data: $('#service-editor-form').serialize(),
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
