/*
global
alertify: false
call: false
fCall: false
fields: false
pools: false
*/

let poolId = null;
const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add pool to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {properties} properties - Properties of the pool.
 */
function addPool(mode, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showPoolModal('${properties.id}')">Edit properties</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showPoolObjects('${properties.id}')">Edit objects</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deletePool('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

(function() {
  $('#doc-link').attr(
    'href',
    'https://enms.readthedocs.io/en/latest/inventory/pools.html'
  );
  for (let i = 0; i < pools.length; i++) {
    addPool('create', pools[i]);
  }
})();

/**
 * Open pool modal for creation.
 */
function showModal() { // eslint-disable-line no-unused-vars
  $('#title').text('Create a New Pool');
  $('#edit-form').trigger('reset');
  $('#edit').modal('show');
}

/**
 * Display pool modal for editing.
 * @param {id} id - Id of the pool to edit.
 */
function showPoolModal(id) { // eslint-disable-line no-unused-vars
  call(`/objects/get/pool/${id}`, function(result) {
    for (const [property, value] of Object.entries(result)) {
      if (property.includes('regex')) {
        $(`#${property}`).prop('checked', value);
      } else {
        $(`#${property}`).val(value);
      }
      $('#title').text(`Edit Pool '${result.name}'`);
    }
    $('#edit').modal('show');
  });
}

/**
 * Display pool objects for editing.
 * @param {id} id - Id of the pool.
 */
function showPoolObjects(id) { // eslint-disable-line no-unused-vars
  call(`/objects/get/pool/${id}`, function(result) {
    $('#devices').val(result.devices.map((n) => n.id));
    $('#links').val(result.links.map((l) => l.id));
    poolId = id;
    $('#edit-pool-objects').modal('show');
  });
}

/**
 * Update pool objects.
 */
function savePoolObjects() { // eslint-disable-line no-unused-vars
  const url = `/objects/save_pool_objects/${poolId}`;
  fCall(url, '#pool-objects-form', function(result) {
    alertify.notify('Changes saved.', 'success', 5);
    $('#edit-pool-objects').modal('hide');
  });
}

/**
 * Update pool properties.
 */
function savePool() { // eslint-disable-line no-unused-vars
  fCall('/objects/process_pool', '#edit-form', function(pool) {
    const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
    addPool(mode, pool);
    const message = `Pool '${pool.name}'
    ${mode == 'edit' ? 'edited !' : 'created !'}.`;
    alertify.notify(message, 'success', 5);
    $('#edit').modal('hide');
  });
}

/**
 * Delete pool.
 * @param {id} id - Id of the pool to delete.
 */
function deletePool(id) { // eslint-disable-line no-unused-vars
  call(`/objects/delete_pool/${id}`, function(name) {
    table.row($(`#${id}`)).remove().draw(false);
    alertify.notify(`Pool '${name}' successfully deleted.`, 'error', 5);
  });
}

/**
 * Update all pool objects according to pool properties.
 */
function updatePools() { // eslint-disable-line no-unused-vars
  call('/objects/update_pools', function(result) {
    alertify.notify('Pools successfully updated.', 'success', 5);
  });
}
