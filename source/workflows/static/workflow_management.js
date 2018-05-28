var workflowId = null
    table = $('#table').DataTable()
    fields = ['name', 'description', 'type'];

function showSchedulingModal(id){
  workflowId = id;
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

function showModal(type) {
  $('#title').text("Add a new workflow");
  $('#edit-form').trigger("reset");
  $('#edit').modal('show');
}

function showWorkflowModal(id) {
  workflowId = id;
  $('#title').text(`Edit properties`);
  $.ajax({
    type: "POST",
    url: `/workflows/get_${workflowId}`,
    success: function(properties){
      for (const [property, value] of Object.entries(properties)) {
        console.log(property, value);
        $(`#property-${property}`).val(value);
      }
    }
  });
  $(`#edit`).modal('show');
}

function editObject() {
  var mode = $('#title').text() == `Edit properties` ? 'edit' : 'add'
  var result = {}
      values = [];
  $.each($("#edit-form").serializeArray(), function() {
    result[this.name] = this.value;
  });

  for (i = 0; i < fields.length; i++) {
    values.push(`${result[fields[i]]}`);
  }

  values.push(
    `<button type="button" class="btn btn-info btn-xs" onclick="showWorkflowModal('${workflowId}')">Edit</button>`,
    `<a href="/workflows/manage_${workflowId}" class="btn btn-info btn-xs">
      <i class="fa fa-pencil"></i>Manage
    </a>`,
    `<button type="button" class="btn btn-primary btn-xs" onclick="showSchedulingModal('${workflowId}')">Run</button>`,
    `<button type="button" class="btn btn-danger btn-xs" onclick="deleteObject('${workflowId}')">Delete</button>`,
  );

  if ($("#edit-form").parsley().validate() ) {
    $.ajax({
      type: "POST",
      url: `/workflows/edit_workflow`,
      dataType: "json",
      data: $("#edit-form").serialize(),
      success: function(name){
        if (mode == 'edit') {
          table.row($(`#${workflowId}`)).data(values);
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

function deleteObject(id) {
  table.row($(`#${id}`)).remove().draw(false);
  $.ajax({
    type: "POST",
    url: `/workflows/delete_${id}`,
    success: function(name){
      alertify.notify(`Workflow ${name} deleted`, 'error', 5);
    }
  });
}