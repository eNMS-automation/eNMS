/*
global
changeMarker: false
connectionParametersModal: false
convertSelect: false
createNode: false
createLink: false
deviceAutomationModal: false
deleteAll: false
doc: false
fCall: false
partial: false
showModal: false
showTypePanel: false
switchLayer: false
switchView: false
currentView: false
*/

/**
 * Update current view.
 */
// eslint-disable-next-line
function updateView() {
  $("#restrict-pool").change();
}

$("#restrict-pool").on("change", function() {
  fCall("/inventory/pools_objects", "#pool-restriction-form", function(
    objects
  ) {
    deleteAll();
    objects.devices.map((d) => createNode(d, "device"));
    objects.links.map(createLink);
  });
});

(function() {
  doc("https://enms.readthedocs.io/en/latest/views/geographical_view.html");
  convertSelect("#restrict-pool");
  $("#restrict-pool").selectpicker("selectAll");
  switchView(currentView);
})();
