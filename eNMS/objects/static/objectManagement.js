/*
global
links: false
linkFields: false
nodes: false
nodeFields: false
*/

const nodeTable = $('#node-table').DataTable(); // eslint-disable-line new-cap
const linkTable = $('#link-table').DataTable(); // eslint-disable-line new-cap

/**
 * Add object to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {type} type - Node or link.
 * @param {properties} properties - Properties of the object.
 */
function addObjectToTable(mode, type, properties) {
  let values = [];
  const table = type == 'node' ? nodeTable : linkTable;
  const fields = type == 'node' ? nodeFields : linkFields;
  for (let i = 0; i < fields.length; i++) {
    if (['longitude', 'latitude'].includes(fields[i])) {
      values.push(`${parseFloat(properties[fields[i]]).toFixed(2)}`);
    } else {
      values.push(`${properties[fields[i]]}`);
    }
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showObjectModal('${type}', '${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteObject('${type}', '${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${type}-${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${type}-${properties.id}`);
  }
}

(function() {
  for (let i = 0; i < nodes.length; i++) {
    addObjectToTable('create', 'node', nodes[i]);
  }
  for (let i = 0; i < links.length; i++) {
    addObjectToTable('create', 'link', links[i]);
  }
})();

document.getElementById('file').onchange = function() {
  $('#form').submit();
};

/**
 * Display the object modal.
 * @param {type} type - Node or link.
 */
function showModal(type) { // eslint-disable-line no-unused-vars
  $('#title').text(`Add a new ${type}`);
  $(`#edit-${type}-form`).trigger('reset');
  $(`#edit-${type}`).modal('show');
}
