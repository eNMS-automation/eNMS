/*
global
addInstance: false
call: false
convertSelect: false
fCall: false
nodes: false
processInstance: false
runJob: false
saveInstance: false
servicesClasses: false
workflowBuilder: false;
*/

(function() {
  convertSelect('#service-devices', '#service-pools');
  for (let i = 0; i < servicesClasses.length; i++) {
    const cls = servicesClasses[i];
    $('#service-type').append(`<option value='${cls}'>${cls}</option>`);
  }
  $('#service-type').change(function() {
    editService();
  });
  $('#edit-service').on('hidden.bs.modal', function() {
    $('#service-type').prop('disabled', false);
  });
})();

/**
 * Edit a service.
 * @param {id} id - Service Id.
 * @param {duplicate} duplicate - Duplicate.
 */
function editService(id, duplicate) {
  const url = `/automation/get_service/${id || $('#service-type').val()}`;
  if (id) $('#service-type').prop('disabled', true);
  call(url, function(r) {
    for (const type of ['boolean', 'list']) {
      const fields = $(`#service-${type}_fields`);
      const prop = type == 'boolean' ? r.boolean_properties : r.list_properties;
      fields.val(`${fields.val()},${prop}`);
    }
    $('#html-form').html(r.form);
    if (r.service) processInstance('service', r.service, duplicate);
  });
}

/**
 * Save a service.
 * @param {run} run - Run after saving.
 */
function saveService(run=false) { // eslint-disable-line no-unused-vars
  fCall(
    `/update/${$('#service-type').val()}`,
    '#edit-service-form',
    function(service) {
      const mode = saveInstance('service', service, !run);
      if (typeof workflowBuilder === 'undefined') {
        addInstance(mode, 'service', service);
      } else {
        nodes.update({id: service.id, label: service.name});
      }
      if (run) {
        runJob(service.id);
      }
    }
  );
}
