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
showTypePanel: false
*/

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
 * Update pool objects.
 */
// eslint-disable-next-line
function savePoolObjects(id) {
  fCall(`/inventory/save_pool_objects/${id}`, `#${id}-pool-objects-form`, function() {
    alertify.notify("Changes saved.", "success", 5);
    $(`#pool-object-panel-${id}`).remove();
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
})();
