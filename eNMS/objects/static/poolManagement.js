/*
global
alertify: false
call: false
doc: false
fCall: false
fields: false
pools: false
*/

let poolId = null;
const table = $('#table').DataTable(); // eslint-disable-line new-cap

function tableActions(values, pool) {
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('pool', '${pool.id}')">Edit properties</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('pool', '${pool.id}', true)">Duplicate</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showPoolObjects('${pool.id}')">Edit objects</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteInstance('pool', '${pool.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/pools.html');
  for (let i = 0; i < pools.length; i++) {
    addInstance('create', 'pool', pools[i]);
  }
})();

/**
 * Display pool objects for editing.
 * @param {id} id - Id of the pool.
 */
function showPoolObjects(id) { // eslint-disable-line no-unused-vars
  call(`/get/pool/${id}`, function(pool) {
    $('#devices').val(pool.devices.map((n) => n.id));
    $('#links').val(pool.links.map((l) => l.id));
    poolId = id;
    $('#edit-pool-objects').modal('show');
  });
}

/**
 * Update pool objects.
 */
function savePoolObjects() { // eslint-disable-line no-unused-vars
  const url = `/objects/save_pool_objects/${poolId}`;
  fCall(url, '#pool-objects-form', function() {
    alertify.notify('Changes saved.', 'success', 5);
    $('#edit-pool-objects').modal('hide');
  });
}

/**
 * Update all pool objects according to pool properties.
 */
function updatePools() { // eslint-disable-line no-unused-vars
  call('/objects/update_pools', function() {
    alertify.notify('Pools successfully updated.', 'success', 5);
  });
}
