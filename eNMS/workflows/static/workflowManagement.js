/*
global
alertify: false
fields: false
workflows: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add workflow to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {properties} properties - Properties of the workflow.
 */
function addWorkflow(mode, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
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
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

(function() {
  for (let i = 0; i < workflows.length; i++) {
    addWorkflow('create', workflows[i]);
  }
})();

/**
 * Open the scheduling modal (disable job section: we schedule the workflow).
 * @param {id} id - Id of the workflow to schedule.
 */
function showSchedulingModal(id) { // eslint-disable-line no-unused-vars
  $('#job-div').hide();
  $('#job').val(id);
  $('#scheduling').modal('show');
}

/**
 * Open the workflow modal for creation.
 */
function showModal() { // eslint-disable-line no-unused-vars
  $('#title').text('Add a new workflow');
  $('#edit-form').trigger('reset');
  $('#edit').modal('show');
}

/**
 * Open the workflow modal for editing.
 * @param {id} id - Id of the workflow to edit.
 */
function showWorkflowModal(id) { // eslint-disable-line no-unused-vars
  $('#title').text(`Edit properties`);
  $.ajax({
    type: 'POST',
    url: `/workflows/get/${id}`,
    success: function(properties) {
      for (const [property, value] of Object.entries(properties)) {
        $(`#property-${property}`).val(value);
      }
    },
  });
  $(`#edit`).modal('show');
}

/**
 * Edit a workflow.
 */
function editObject() { // eslint-disable-line no-unused-vars
  if ($('#edit-form').parsley().validate() ) {
    $.ajax({
      type: 'POST',
      url: `/workflows/edit_workflow`,
      dataType: 'json',
      data: $('#edit-form').serialize(),
      success: function(properties) {
        const mode = $('#title').text() == `Edit properties` ? 'edit' : 'add';
        addWorkflow(mode, properties);
        const message = `Workflow ${properties.name};
        ${mode == 'edit' ? 'edited' : 'created'}.`;
        alertify.notify(message, 'success', 5);
      },
    });
    $(`#edit`).modal('hide');
  }
}

/**
 * Delete a workflow.
 * @param {id} id - Id of the workflow to delete.
 */
function deleteWorkflow(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/workflows/delete/${id}`,
    success: function(name) {
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify(`Workflow '${name}' deleted.`, 'error', 5);
    },
  });
}
