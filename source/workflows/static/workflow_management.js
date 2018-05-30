/*jshint esversion: 6 */

var workflowId = null;
var table = $('#table').DataTable();
var fields = ['name', 'description', 'type'];

// Scheduling: run a workflow

function showSchedulingModal(id){
  workflowId = id;
  $("#scheduling").modal('show');
}

function scheduleScript() {
  if ($("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: `/tasks/job_scheduler/workflow/${workflowId}`,
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

// Properties modal: add or edit a workflow

// open modal to add a new workflow
function showModal(type) {
  $('#title').text("Add a new workflow");
  $('#edit-form').trigger("reset");
  $('#edit').modal('show');
}

// open modal to edit an existing workflow
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
  if ($("#edit-form").parsley().validate() ) {
    $.ajax({
      type: "POST",
      url: `/workflows/edit_workflow`,
      dataType: "json",
      data: $("#edit-form").serialize(),
      success: function(properties){
        var result = {};
        var mode = $('#title').text() == `Edit properties` ? 'edit' : 'add';
        var values = [];
        $.each($("#edit-form").serializeArray(), function() {
          result[this.name] = this.value;
        });
        for (i = 0; i < fields.length; i++) {
          values.push(`${result[fields[i]]}`);
        }
        values.push(
          `<button type="button" class="btn btn-info btn-xs" onclick="showWorkflowModal('${properties.id}')">Edit</button>`,
          `<a href="/workflows/manage_${properties.id}" class="btn btn-info btn-xs">
            <i class="fa fa-pencil"></i>Manage
          </a>`,
          `<button type="button" class="btn btn-primary btn-xs" onclick="showSchedulingModal('${properties.id}')">Run</button>`,
          `<button type="button" class="btn btn-danger btn-xs" onclick="deleteObject('${properties.id}')">Delete</button>`
        );
        if (mode == 'edit') {
          table.row($(`#${properties.id}`)).data(values);
        } else {
          table.row.add(values).draw(false).node();
          $(rowNode).attr("id", `${properties.id}`);
        }
        message = `Workflow ${properties.name} ` + (mode == 'edit' ? 'edited !' : 'created !');
        alertify.notify(message, 'success', 5);
      }
    });
    $(`#edit`).modal('hide');
  }
}

// delete a workflow
function deleteObject(id) {
  $.ajax({
    type: "POST",
    url: `/workflows/delete_${id}`,
    success: function(name){
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify(`Workflow ${name} deleted`, 'error', 5);
    }
  });
}