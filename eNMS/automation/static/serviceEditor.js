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
  convertSelect('service-devices', 'service-pools');
  for (let i = 0; i < servicesClasses.length; i++) {
    const cls = servicesClasses[i];
    $('#services').append(`<option value='${cls}'>${cls}</option>`);
  }
  $('#services').change(function() {
    editService();
  });
})();

/**
 * Edit a service.
 * @param {id} id - Service Id.
 * @param {duplicate} duplicate - Duplicate.
 */
function editService(id, duplicate) {
  const url = `/automation/get_service/${id || $('#services').val()}`;
  call(url, function(result) {
    if (result.service) processInstance('service', result.service, duplicate);
    $('#html-form').html(result.form);
  });
}

/**
 * Save a service.
 */
function saveService() { // eslint-disable-line no-unused-vars
  const url = `/automation/save_service/${$('#services').val()}`;
  fCall(url, '#edit-service-form', function(result) {
    mode = saveInstance(type, instance);
    if (typeof workflowBuilder === 'undefined') {
      addService(mode, result);
    } else {
      nodes.update({id: result.id, label: result.name});
    }
  });
}
