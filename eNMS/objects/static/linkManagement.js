/*
global
addObjectToTable: false
doc: false
links: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

function tableActions(values, pool) {
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('link', '${obj.id}')">Edit</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('link', '${obj.id}', true)">
    Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteInstance('link', '${obj.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  for (let i = 0; i < links.length; i++) {
    addInstance('create', 'link', links[i]);
  }
})();
