/*
global
addObjectToTable: false
devices: false
doc: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

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
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  for (let i = 0; i < devices.length; i++) {
    addInstance('create', 'device', devices[i]);
  }
})();
