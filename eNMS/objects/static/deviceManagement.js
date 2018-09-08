/*
global
links: false
linkFields: false
nodes: false
nodeFields: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add object to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {type} type - Node or link.
 * @param {properties} properties - Properties of the object.
 */
function addObjectToTable(mode, type, properties) {
  let values = [];
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
})();

document.getElementById('file').onchange = function() {
  $('#form').submit();
};

/**
 * Display the node modal.
 */
function showModal() { // eslint-disable-line no-unused-vars
  $('#title').text('Add a new node');
  $('#edit-node-form').trigger('reset');
  $('#edit-node').modal('show');
}
