/*jshint esversion: 6 */

var table = $('#table').DataTable();

function addWorkflow(mode, properties) {
  var values = [];
  for (var i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showWorkflowModal('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showSchedulingModal('${properties.id}')">Schedule</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteWorkflow('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    var rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr("id", `${properties.id}`);
  }
}

(function() {
  for (var i = 0; i < workflows.length; i++) {
    addWorkflow('create', workflows[i]);
  }
})();

// Scheduling: run a workflow

function showSchedulingModal(id) {
  $("#job-div").hide()
  $("#job").val(id);
  $("#scheduling").modal('show');
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
  $('#title').text(`Edit properties`);
  $.ajax({
    type: "POST",
    url: `/workflows/get/${id}`,
    success: function(properties){
      for (const [property, value] of Object.entries(properties)) {
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
        var mode = $('#title').text() == `Edit properties` ? 'edit' : 'add';
        addWorkflow(mode, properties);
        message = `Workflow ${properties.name}
        ${mode == 'edit' ? 'edited' : 'created'}.`;
        alertify.notify(message, 'success', 5);
      }
    });
    $(`#edit`).modal('hide');
  }
}

// delete a workflow
function deleteWorkflow(id) {
  $.ajax({
    type: "POST",
    url: `/workflows/delete/${id}`,
    success: function(name){
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify(`Workflow '${name}' deleted.`, 'error', 5);
    }
  });
}