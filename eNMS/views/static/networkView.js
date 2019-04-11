/*
global
call: false
connectionParametersModal: false
createNode: false
createLink: false
deviceAutomationModal: false
deleteAll: false
doc: false
partial: false
showModal: false
showTypeModal: false
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
  fCall("/inventory/pool_objects", "#pool-restriction-form", function(objects) {
    deleteAll();
    objects.devices.map((d) => createNode(d, "device"));
    objects.links.map(createLink);
  });
});

// eslint-disable-next-line no-unused-vars
const action = {
  "Export to Google Earth": partial(showModal, "google-earth"),
  "Open Street Map": partial(switchLayer, "osm"),
  "Google Maps": partial(switchLayer, "gm"),
  NASA: partial(switchLayer, "nasa"),
  "Device properties": (d) => showTypeModal("device", d),
  "Link properties": (l) => showTypeModal("link", l),
  "Pool properties": (p) => showTypeModal("pool", p),
  Connect: connectionParametersModal,
  Automation: deviceAutomationModal,
};

(function() {
  doc("https://enms.readthedocs.io/en/latest/views/geographical_view.html");
  $("#restrict-pool").selectpicker("selectAll");
  switchView(currentView);
})();
