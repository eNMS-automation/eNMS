var workflow = null;
function showSchedulingModal(workflowName){
  workflow = workflowName;
  $("#scheduling").modal('show');
}

function scheduleScript() {
  if ($("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: `/tasks/job_scheduler/workflow/${workflow}`,
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

var table = $('#table').DataTable();

function showModal(type) {
  $('#title').text("Add a new workflow");
  $('#edit-form').trigger("reset");
  $('#edit').modal('show');
}

function showObjectModal(name) {
  $('#title').text(`Edit properties`);
  $.ajax({
    type: "POST",
    url: `/workflows/get_${name}`,
    success: function(properties){
      for (const [property, value] of Object.entries(properties)) {
        $(`#${property}`).val(value);
      }
    }
  });
  $(`#edit`).modal('show');
}

var fields = ['name', 'description', 'type'];
function editObject() {
  var mode = $('#title').text() == `Edit properties` ? 'edit' : 'add'
  var result = {}
      values = [];
  $.each($("#edit-form").serializeArray(), function() {
    result[this.name] = this.value;
  });

  var name = result.name;
  for (i = 0; i < fields.length; i++) {
    values.push(`${result[fields[i]]}`);
  }

  values.push(
    `<button type="button" class="btn btn-info btn-xs" onclick="showObjectModal('${name}')">Edit</button>`,
    `<a href="/workflows/manage_${name}" class="btn btn-info btn-xs">
      <i class="fa fa-pencil"></i>Manage
    </a>`,
    `<button type="button" class="btn btn-primary btn-xs" onclick="showSchedulingModal('${name}')">Run</button>`,
    `<button type="button" class="btn btn-danger btn-xs" onclick="deleteObject('${name}')">Delete</button>`,
  );

  if ($("#edit-form").parsley().validate() ) {
    $.ajax({
      type: "POST",
      url: `/workflows/edit_workflow`,
      dataType: "json",
      data: $("#edit-form").serialize(),
      success: function(msg){
        if (mode == 'edit') {
          $(`#${name}`).html(values.join(''));
        } else {
          table.row.add(values).draw(false);
        }
        message = `Workflow ${name} ` + (mode == 'edit' ? 'edited !' : 'created !')
        alertify.notify(message, 'success', 5);
      }
    });
    $(`#edit`).modal('hide');
  }
}

function deleteObject(name) {
  table.row($(`#${name}`)).remove().draw(false);
  $.ajax({
    type: "POST",
    url: `/workflows/delete_${name}`,
    success: function(msg){
      alertify.notify(`Workflow ${name} deleted`, 'error', 5);
    }
  });
}