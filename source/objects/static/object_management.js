var nodeTable = $('#node-table').DataTable();
var linkTable = $('#link-table').DataTable();

function addObject(mode, type, properties) {
  var values = [];
  var table = type == 'node' ? nodeTable : linkTable;
  var fields = type == 'node' ? node_fields : link_fields
  for (var i = 0; i < fields.length; i++) {
    var truncate = ["longitude", "latitude"].includes(fields[i]);
    value = truncate ? parseFloat(properties[fields[i]]).toFixed(2) : properties[fields[i]]
    values.push(`${value}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs" onclick="showObjectModal('${type}', '${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs" onclick="deleteObject('${type}', '${properties.id}')">Delete</button>`,
  );
  if (mode == 'edit') {
    table.row($(`#${type}-${properties.id}`)).data(values);
  } else {
    var rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr("id", `${type}-${properties.id}`);
  }
}

(function() {
  for (var i = 0; i < nodes.length; i++) {
    addObject('create', 'node', nodes[i]);
  }
  for (var i = 0; i < links.length; i++) {
    addObject('create', 'link', links[i]);
  }
})();

document.getElementById("file").onchange = function() {
  $("#form").submit();
};

function showModal(type) {
  $('#title').text(`Add a new ${type}`);
  $(`#edit-${type}-form`).trigger("reset");
  $(`#edit-${type}`).modal('show');
}