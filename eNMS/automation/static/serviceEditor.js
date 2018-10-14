/*
global
addService: false
alertify: false
propertyTypes: false
servicesClasses: false
showModal: false
workflowBuilder: false;
*/

(function() {
  for (let i = 0; i < servicesClasses.length; i++) {
    const cls = servicesClasses[i];
    $('#services').append(`<option value='${cls}'>${cls}</option>`);
  }
})();

/**
 * Show the Service Editor modal
 */
function showServiceEditor() { // eslint-disable-line no-unused-vars
  $('#title').text('Create a new service');
  $('#services').show();
  $('#service-editor-form').trigger('reset');
  editService();
  $('#service-editor').modal('show');
}

/**
 * Edit a service.
 * @param {id} id - Service Id.
 */
function editService(id) {
  if (id) {
    $('#title').text('Edit service');
  }
  $.ajax({
    type: 'POST',
    url: `/automation/get_service/${id || $('#services').val()}`,
    success: function(result) {
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        $('#html-form').html(result.form);
        if (result.service) {
          $('#services').hide();
          for (const [property, value] of Object.entries(result.service)) {
            const propertyType = propertyTypes[property] || 'str';
            if (propertyType.includes('bool')) {
              $(`#${property}`).prop('checked', value);
            } else if (propertyType.includes('dict')) {
              $(`#${property}`).val(value ? JSON.stringify(value): '{}');
            } else {
              $(`#${property}`).val(value);
            }
          }
          $('#services').val(result.service.type);
          $('#devices').val(result.service.devices.map((n) => n.id));
          $('#pools').val(result.service.pools.map((p) => p.id));
          showModal('service-editor');
        }
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
          const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
          if (typeof workflowBuilder === 'undefined') {
            addService(mode, service);
          }
          const message = `Service '${service.name}'
          ${mode == 'edit' ? 'edited' : 'created'} !`;
          alertify.notify(message, 'success', 5);
          $('#service-editor').modal('hide');
        }
      },
    });
  }
}

$('#services').change(function() {
  editService();
});
