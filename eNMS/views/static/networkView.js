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
  call("/inventory/pool_objects/1", function(pool) {
    pool.devices.map((d) => createNode(d, "device"));
    pool.links.map(createLink);
  });
}

function filter(type) {
  $.ajax({
    type: "POST",
    url: `/filtering/view/${type}`,
    data: serializeForm(`#${type}-filter-form`),
    success: function(results) {
      console.log(results)
    },
  });
}

(function() {
  doc("https://enms.readthedocs.io/en/latest/views/geographical_view.html");
  switchView(currentView);
})();
