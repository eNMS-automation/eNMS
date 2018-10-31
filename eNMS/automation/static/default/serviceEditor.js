/*
global
addService: false
alertify: false
call: false
fCall: false
nodes: false
propertyTypes: false
servicesClasses: false
showModal: false
workflowBuilder: false;
*/

(function() {
  $('#devices').fSelect({
    placeholder: 'Select devices',
    numDisplayed: 5,
    overflowText: '{n} devices selected',
    noResultsText: 'No results found',
    showSearch: true,
  });
  for (let i = 0; i < servicesClasses.length; i++) {
    const cls = servicesClasses[i];
    $('#services').append(`<option value='${cls}'>${cls}</option>`);
  }
})();

/**
 * Show the Service Editor modal
 */
function showServiceEditor() { // eslint-disable-line no-unused-vars
  $('#title').text('Create a New Service Instance');
  $('#services').show();
  $('#service-editor-form').trigger('reset');
  $('.fs-option').removeClass('selected');
  $('.fs-label').text('Select devices');
  editService();
  $('#service-editor').modal('show');
}

/**
 * Edit a service.
 * @param {id} id - Service Id.
 */
function editService(id) {
  if (id) {
    $('#title').text('Edit Service Instance');
  }
  const url = `/automation/get_service/${id || $('#services').val()}`;
  call(url, function(result) {
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
      $('.fs-option').removeClass('selected');
      $('.fs-label').text('Select devices');
      result.service.devices.map(
        (n) => $(`.fs-option[data-value='${n.id}']`).click()
      );
      $('#pools').val(result.service.pools.map((p) => p.id));
      showModal('service-editor');
    }
  });
}

/**
 * Save a service.
 */
function saveService() { // eslint-disable-line no-unused-vars
  const url = `/automation/save_service/${$('#services').val()}`;
  fCall(url, '#service-editor-form', function(result) {
    if (result == 'JSONDecodeError') {
      const message = `Json Parsing Error: make sure that properties expecting
        dictionnaries have valid Json input.`;
      alertify.notify(message, 'error', 5);
    } else {
      const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
      if (typeof workflowBuilder === 'undefined') {
        addService(mode, result);
      } else {
        nodes.update({id: result.id, label: result.name});
      }
      const message = `Service '${result.name}'
      ${mode == 'edit' ? 'edited' : 'created'} !`;
      alertify.notify(message, 'success', 5);
      $('#service-editor').modal('hide');
    }
  });
}

$('#services').change(function() {
  editService();
});
