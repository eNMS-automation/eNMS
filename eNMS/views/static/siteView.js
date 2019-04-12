/*
global
call: false
changeMarker: false
connectionParametersModal: false
createNode: false
currentView: true
deleteAll: false
deviceAutomationModal: false
displayPool: false
doc: false
partial: false
selected: false
showModal: false
showTypeModal: false
switchLayer: false
switchView: false
*/

/**
 * Display sites (pools with non-empty coordinates).
 */
function displaySites() {
  $(".menu,#network").hide();
  deleteAll();
  call("/get_all/pool", function(pools) {
    for (let i = 0; i < pools.length; i++) {
      if (pools[i].longitude) {
        createNode(pools[i], "site");
      }
    }
  });
  $(".geo-menu").show();
}

/**
 * Enter site.
 * @param {siteId} siteId - Pool ID.
 */
function enterSite(siteId) {
  $("#map,#earth").css("visibility", "hidden");
  $(".menu").hide();
  $(".btn-view").show();
  $("#network,.insite-menu,rc-device-menu,rc-link-menu").show();
  call(`/inventory/pool_objects/${siteId}`, function(objects) {
    displayPool(objects.devices, objects.links);
  });
}

/**
 * Update view.
 */
// eslint-disable-next-line
function updateView() {
  displaySites();
}

const action = {
  // eslint-disable-line no-unused-vars
  "Export to Google Earth": partial(showModal, "google-earth"),
  "Open Street Map": partial(switchLayer, "osm"),
  "Google Maps": partial(switchLayer, "gm"),
  NASA: partial(switchLayer, "nasa"),
  "Device properties": (d) => showTypeModal("device", d),
  "Link properties": (l) => showTypeModal("link", l),
  "Pool properties": (p) => showTypeModal("pool", p),
  Connect: connectionParametersModal,
  Automation: deviceAutomationModal,
  "Display sites": () => switchView(currentView),
  "Enter site": enterSite,
  "2D": partial(switchView, "2D"),
  "Clustered 2D": partial(switchView, "2DC"),
  "3D": partial(switchView, "3D"),
  Image: partial(changeMarker, "Image"),
  Circle: partial(changeMarker, "Circle"),
  "Circle Marker": partial(changeMarker, "Circle Marker"),
};

$("#network").contextMenu({
  menuSelector: "#contextMenu",
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selected);
  },
});

(function() {
  doc("https://enms.readthedocs.io/en/latest/views/geographical_view.html");
  switchView(currentView);
})();
