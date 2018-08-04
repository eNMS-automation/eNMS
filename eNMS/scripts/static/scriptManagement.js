var table = $('#table').DataTable();

function addScript(mode, properties) {
  values = [];
  for (var i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showScriptModal('${properties.type}', '${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showSchedulingModal('${properties.id}')">Schedule</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteScript('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    var rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr("id", `${properties.id}`);
  }
}

(function() {
  for (var i = 0; i < scripts.length; i++) {
    addScript('create', scripts[i]);
  }
})();

// replace the button value of all script forms with "Update"
for (var i = 0; i < types.length; i++) {
  $(`#${types[i]}-button`).text("Update");
}

function showSchedulingModal(id){
  $("#job-div").hide()
  $("#job").val(id);
  $("#scheduling").modal('show');
}

function createScript(type) {
  if ($(`#${type}-form`).parsley().validate() ) {
    $.ajax({
      type: "POST",
      url: `/scripts/create_script/${type}`,
      dataType: "json",
      data: $(`#${type}-form`).serialize(),
      success: function() {
        alertify.notify("Script successfully updated.", 'success', 5);
      }
    });
    $(`#edit-${type}`).modal('hide');
  }
}

function deleteScript(id) {
  $.ajax({
    type: "POST",
    url: `/scripts/delete/${id}`,
    success: function(scriptName){
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify(`Script '${scriptName}' successfully deleted.`, 'error', 5);
    }
  });
}