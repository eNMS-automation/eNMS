/*
global
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
  convertSelect("#service-devices", "#service-pools");

  $("#edit-service").on("hidden.bs.modal", function() {
    $("#service-type").prop("disabled", false);
  });
})();

/**
 * Edit a service.
 * @param {id} id - Service Id.
 * @param {duplicate} duplicate - Duplicate.
 */
function editService(id, duplicate) {
  
  if (id) {
    showTypePanel("service", id, duplicate);
    $("#service-type").prop("disabled", true);
  }

}

/**
 * Save a service.
 * @param {run} run - Run after saving.
 */
// eslint-disable-next-line
function saveService(run) {
  fCall(`/update/${$("#service-type").val()}`, "#edit-service-form", function(
    service
  ) {
    saveInstance("service", service, !run);
    if (typeof workflowBuilder !== "undefined") {
      nodes.update({ id: service.id, label: service.name });
    }
    if (run) {
      runJob(service.id);
    }
  });
}
