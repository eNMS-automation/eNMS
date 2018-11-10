/*
global
addInstance: false
call: false
convertSelect: false
fCall: false
nodes: false
processInstance: false
saveInstance: false
servicesClasses: false
workflowBuilder: false;
*/

(function() {
  convertSelect('service-devices', 'service-pools');
  for (let i = 0; i < servicesClasses.length; i++) {
    const cls = servicesClasses[i];
    $('#service-type').append(`<option value='${cls}'>${cls}</option>`);
  }
  $('#service-type').change(function() {
    editService();
  });
})();

/**
 * Edit a service.
 * @param {id} id - Service Id.
 * @param {duplicate} duplicate - Duplicate.
 */
function editService(id, duplicate) {
  const url = `/automation/get_service/${id || $('#service-type').val()}`;
  call(url, function(result) {
    $('#html-form').html(result.form);
    if (result.service) processInstance('service', result.service, duplicate);
  });
}

/**
 * Save a service.
 */
function saveService() { // eslint-disable-line no-unused-vars
  fCall(
    `/update/${$('#service-type').val()}`,
    '#edit-service-form',
    function(service) {
      const mode = saveInstance('service', service);
      if (typeof workflowBuilder === 'undefined') {
        addInstance(mode, 'service', service);
      } else {
        nodes.update({id: service.id, label: service.name});
      }
    }
  );
}
