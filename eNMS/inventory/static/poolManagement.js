/*
global
addInstance: false
alertify: false
call: false
convertSelect: false
doc: false
fCall: false
pools: false
*/

const table = $('#table').DataTable({ // eslint-disable-line
  ordering: false,
  fixedHeader: true,
  processing: true,
  serverSide: true,
  ajax: '/server_side_processing/pool/pool',
});
let poolId = null;

/**
 * Display pool objects for editing.
 * @param {id} id - Id of the pool.
 */
function showPoolObjects(id) { // eslint-disable-line no-unused-vars
  call(`/get/pool/${id}`, function(pool) {
    $('#devices,#links').selectpicker('deselectAll');
    $('#devices').selectpicker('val', pool.devices.map((n) => n.id));
    $('#links').selectpicker('val', pool.links.map((l) => l.id));
    poolId = id;
    $('#edit-pool-objects').modal('show');
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
