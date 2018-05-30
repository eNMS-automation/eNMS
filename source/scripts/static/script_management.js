var scriptId = null
var table = $('#table').DataTable()

function addScript(mode, properties) {
  values = [];
  for (j = 0; j < fields.length; j++) {
    values.push(`${properties[fields[j]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs" onclick="showScriptModal('${properties.type}', '${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs" onclick="showSchedulingModal('${properties.id}')">Run</button>`,
    `<button type="button" class="btn btn-danger btn-xs" onclick="deleteScript('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    var rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr("id", `${properties.id}`);
  }
}

(function() {
  for (i = 0; i < scripts.length; i++) {
    addScript('create', scripts[i]);
  }
})();

// replace the button value of all script forms with "Update"
for (i = 0; i < types.length; i++) {
  $(`#${types[i]}-button`).text("Update");
}

function showSchedulingModal(id){
  scriptId = id;
  $("#scheduling").modal('show');
}

function scheduleScript() {
  if ($("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: `/tasks/job_scheduler/script/${scriptId}`,
      dataType: "json",
      data: $("#scheduling-form").serialize(),
      success: function() {
        alertify.notify('Task scheduled', 'success', 5);
      }
    });
    $("#scheduling").modal('hide');
  } else {
    alertify.notify('Some fields are missing', 'error', 5);
  }
}

function showScriptModal(type, id) {
  $.ajax({
    type: "POST",
    url: `/scripts/get/${type}/${id}`,
    success: function(properties){
      $('#title').text(`Edit ${properties.name} properties`);
      for (const [property, value] of Object.entries(properties)) {
        if(typeof(value) === "boolean") {
          $(`#${type}-${property}`).prop('checked', value);
        } else {
          $(`#${type}-${property}`).val(value);
        }
      }
    }
  });
  $(`#edit-${type}`).modal('show');
}

function createScript(type) {
  if ($(`#${type}-form`).parsley().validate() ) {
    $.ajax({
      type: "POST",
      url: `/scripts/create_script_${type}`,
      dataType: "json",
      data: $(`#${type}-form`).serialize(),
      success: function() {
        alertify.notify("Script updated", 'success', 5);
      }
    });
    $(`#edit-${type}`).modal('hide');
  }
}

function deleteScript(id) {
  $.ajax({
    type: "POST",
    url: `/scripts/delete_${id}`,
    success: function(scriptName){
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify(`Script ${scriptName} deleted`, 'error', 5);
    }
  });
}