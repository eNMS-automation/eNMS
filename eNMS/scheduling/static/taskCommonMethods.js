/*
global
call: false
*/

/**
 * Show the task modal for task.
 * @param {id} id - Task id.
 */
function showTaskModal(id) { // eslint-disable-line no-unused-vars
  if (!id) {
    $('#title').text('Create a New Task');
    $('#task-modal-form').trigger('reset');
    $('#task-modal').modal('show');
  } else {
    call(`/scheduling/get/${id}`, function(properties) {
      for (const [property, value] of Object.entries(properties)) {
        $(`#${property}`).val(value);
      }
      $('#job').val(properties.job.id);
      $('#title').text(`Edit Task '${properties.name}'`);
    });
  }
  $('#task-modal').modal('show');
}
