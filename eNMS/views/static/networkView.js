/*
global
call: false
connectionParametersModal: false
createNode: false
createLink: false
deviceAutomationModal: false
deleteAll: false
doc: false
map: false
markers: true
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
  $("#pool-filter").change();
}

$("#pool-filter").on("change", function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    deleteAll();
    objects.devices.map((d) => createNode(d, "device"));
    objects.links.map(createLink);
    if (currentView == "2DC") {
      map.addLayer(markers);
    }
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
  $("#network").hide();
  switchView(currentView);
})();
