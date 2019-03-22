/*
global
alertify: false
call: false
convertSelect: false
doc: false
fCall: false
initTable: false
*/

let poolId = null;
let table = initTable( // eslint-disable-line no-unused-vars
  'pool', 'pool', [
  'Number of objects',
  'Edit properties',
  'Update',
  'Duplicate',
  'Edit objects',
  'Delete',
]);

/**
 * Display pool objects for editing.
 * @param {id} id - Id of the pool.
 */
function showPoolObjects(id) { // eslint-disable-line no-unused-vars
  call(`/get/pool/${id}`, function(pool) {
    $('#devices,#links').selectpicker('deselectAll');
    $('#devices').selectpicker('val', pool.devices.map((n) => n.id));
    $('#links').selectpicker('val', pool.links.map((l) => l.id));
    
    $('#edit-pool-objects').modal('show');
  });
}

$('#view-pool').on('shown.bs.modal', function() {
  call(`/inventory/pool_objects/${poolId}`, function(pool) {
    displayPool(pool.devices, pool.links);
  });
});

/**
 * Visualize pool.
 * @param {id} id - Id of the pool.
 */
function showPoolView(id) { // eslint-disable-line no-unused-vars
  poolId = id;
  call(`/inventory/pool_objects/${id}`, function(pool) {
    eraseNetwork();
    $('#view-pool').modal('show');
  });
}

/**
 * Update pool objects.
 */
function savePoolObjects() { // eslint-disable-line no-unused-vars
  const url = `/inventory/save_pool_objects/${poolId}`;
  fCall(url, '#pool-objects-form', function() {
    alertify.notify('Changes saved.', 'success', 5);
    $('#edit-pool-objects').modal('hide');
  });
}

/**
 * Update one or all pools.
 * @param {pool} pool - Id of a pool or 'all'.
 */
function updatePool(pool) { // eslint-disable-line no-unused-vars
  call(`/inventory/update_pool/${pool}`, function() {
    alertify.notify('Update successful.', 'success', 5);
  });
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/pools.html');
  convertSelect('#links', '#devices');
})();
