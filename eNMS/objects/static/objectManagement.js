/*
global
links: false
link_fields: false
nodes: false
node_fields: false
*/

const nodeTable = $('#node-table').DataTable(); // eslint-disable-line new-cap
const linkTable = $('#link-table').DataTable(); // eslint-disable-line new-cap

function addObjectToTable(mode, type, properties) {
  let values = [];
  const table = type == 'node' ? nodeTable : linkTable;
  const fields = type == 'node' ? node_fields : link_fields;
  for (let i = 0; i < fields.length; i++) {
    if (['longitude', 'latitude'].includes(fields[i])) {
      value = parseFloat(properties[fields[i]]).toFixed(2);
    } else {
      properties[fields[i]];
    }
    values.push(`${value}`);
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
    rowNode = table.row.add(values).draw(false).node();
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

function showModal(type) {
  $('#title').text(`Add a new ${type}`);
  $(`#edit-${type}-form`).trigger('reset');
  $(`#edit-${type}`).modal('show');
}
