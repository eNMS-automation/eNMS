/*
global
changeMarker: false
connectionParametersModal: false
createNode: false
createLink: false
deviceAutomationModal: false
deleteAll: false
doc: false
fCall: false
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
  call("/get-pool-1", function(pool) {
    pool.devices.map((d) => createNode(d, "device"));
    pool.links.map(createLink);
  });
}

function filter(type) {
  fCall(`/view_filtering/${type}`, `#${type}-form`, (r) => {
    if (type == "device_filtering") {
      deleteAllDevices();
      r.map((d) => createNode(d, "device"));
    } else {
      deleteAllLinks();
      r.map(createLink);
    }
  });
}

(function() {
  doc("https://enms.readthedocs.io/en/latest/views/geographical_view.html");
  switchView(currentView);
})();
