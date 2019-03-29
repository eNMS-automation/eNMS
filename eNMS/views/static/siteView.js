/*
global
alertify: false
call: false
connectionParametersModal: false
createNode: false
deleteAll: false
deviceAutomationModal: false
displayPool: false
doc: false
partial: false
selected: false
showModal: false
showTypeModal: false
switchLayer: false
*/

/**
 * Display sites (pools with non-empty coordinates).
 */
function displaySites() {
  // eslint-disable-line no-unused-vars
  $(".menu,#network").hide();
  deleteAll();
  call("/get_all/pool", function(pools) {
    for (let i = 0; i < pools.length; i++) {
      if (pools[i].longitude) {
        createNode(pools[i], "pool");
      }
    }
  });
  $(".geo-menu,.rc-pool-menu").show();
  alertify.notify("Site view");
}

/**
 * Enter pool.
 * @param {poolId} poolId - Pool ID.
 */
function enterPool(poolId) {
  // eslint-disable-line no-unused-vars
  $("#map,#earth").css("visibility", "hidden");
  $(".menu").hide();
  $("#network,.insite-menu,rc-device-menu,rc-link-menu").show();
  call(`/inventory/pool_objects/${poolId}`, function(objects) {
    alertify.notify("Loading the view...", 3);
    displayPool(objects.devices, objects.links);
  });
}

/**
 * Update view.
 */
// eslint-disable-next-line
function updateView() {
  // eslint-disable-line no-unused-vars
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
  "Display pools": displaySites,
  "Enter pool": enterPool,
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
  displaySites();
})();
