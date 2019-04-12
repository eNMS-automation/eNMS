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
  fCall("/inventory/pools_objects", "#pool-restriction-form", function(
    objects
  ) {
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
  "2D": partial(switchView, "2D"),
  "Clustered 2D": partial(switchView, "2DC"),
  "3D": partial(switchView, "3D"),
  Image: partial(changeMarker, "Image"),
  Circle: partial(changeMarker, "Circle"),
  "Circle Marker": partial(changeMarker, "Circle Marker"),
};

(function() {
  doc("https://enms.readthedocs.io/en/latest/views/geographical_view.html");
  convertSelect("#restrict-pool");
  $("#restrict-pool").selectpicker("selectAll");
  switchView(currentView);
})();
