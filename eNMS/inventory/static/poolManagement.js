/*
global
alertify: false
call: false
connectionParametersModal: false
convertSelect: false
deviceAutomationModal: false
displayPool: false
doc: false
eraseNetwork: false
fCall: false
initTable: false
selected: false
showTypeModal: false
*/

let poolId = null;

// eslint-disable-next-line no-unused-vars
let table = initTable("pool", "pool", [
  "Number of objects",
  "Visualize",
  "Edit properties",
  "Update",
  "Duplicate",
  "Edit objects",
  "Delete",
]);

/**
 * Display pool objects for editing.
 * @param {id} id - Id of the pool.
 */
// eslint-disable-next-line
function showPoolObjects(id) {
  call(`/get/pool/${id}`, function(pool) {
    $("#devices,#links").selectpicker("deselectAll");
    $("#devices").selectpicker("val", pool.devices.map((n) => n.id));
    $("#links").selectpicker("val", pool.links.map((l) => l.id));
    poolId = id;
    $("#edit-pool-objects").modal("show");
  });
}

$("#view-pool").on("shown.bs.modal", function() {
  call(`/inventory/pool_objects/${poolId}`, function(pool) {
    displayPool(pool.devices, pool.links);
  });
});

/**
 * Visualize pool.
 * @param {id} id - Id of the pool.
 */
// eslint-disable-next-line
function showPoolView(id) {
  poolId = id;
  call(`/inventory/pool_objects/${id}`, function(pool) {
    eraseNetwork();
    $("#view-pool").modal("show");
  });
}

const action = {
  "Device properties": (d) => showTypeModal("device", d),
  "Link properties": (l) => showTypeModal("link", l),
  "Pool properties": (p) => showTypeModal("pool", p),
  Connect: connectionParametersModal,
  Automation: deviceAutomationModal,
};

$("#network").contextMenu({
  menuSelector: "#contextMenu",
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selected);
  },
});

/**
 * Update pool objects.
 */
// eslint-disable-next-line
function savePoolObjects() {
  const url = `/inventory/save_pool_objects/${poolId}`;
  fCall(url, "#pool-objects-form", function() {
    alertify.notify("Changes saved.", "success", 5);
    $("#edit-pool-objects").modal("hide");
  });
}

/**
 * Update one or all pools.
 * @param {pool} pool - Id of a pool or 'all'.
 */
// eslint-disable-next-line
function updatePool(pool) {
  alertify.notify("Update starting...", "success", 5);
  call(`/inventory/update_pool/${pool}`, function() {
    table.ajax.reload(null, false);
    alertify.notify("Update successful.", "success", 5);
  });
}

(function() {
  doc("https://enms.readthedocs.io/en/latest/inventory/pools.html");
  convertSelect("#links", "#devices");
})();
