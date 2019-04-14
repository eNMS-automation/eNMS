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

/**
 * Save a service.
 * @param {run} run - Run after saving.
 */
// eslint-disable-next-line
function saveService(run, id) {
  fCall(
    `/update/${$("#service-type").val()}`,
    id ? "#${id}-edit-service-form" :  "#edit-service-form",
    function(service) {
    saveInstance("service", service, !run);
    if (typeof workflowBuilder !== "undefined") {
      nodes.update({ id: service.id, label: service.name });
    }
    if (run) {
      runJob(service.id);
    }
  });
}

(function() {
  convertSelect("#service-devices", "#service-pools");
})();
