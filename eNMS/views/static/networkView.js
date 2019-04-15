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

}

(function() {
  doc("https://enms.readthedocs.io/en/latest/views/geographical_view.html");
  $("#restrict-pool").selectpicker("selectAll");
  switchView(currentView);
})();
