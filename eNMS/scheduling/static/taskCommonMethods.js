/*
global
call: false
*/

/**
 * Show the task modal for task.
 * @param {id} id - Task id.
 */
function showTaskModal(id, duplicate) { // eslint-disable-line no-unused-vars
  if (!id) {
    $('#title').text('Create a New Task');
    $('#task-modal-form').trigger('reset');
    $('#task-modal').modal('show');
  } else {
    call(`/scheduling/get/${id}`, function(properties) {
      $('#title').text(`Edit Task '${properties.name}'`);
      for (const [property, value] of Object.entries(properties)) {
        $(`#${property}`).val(value);
      }
      $('#job').val(properties.job.id);
    });
  }
  $('#task-modal').modal('show');
}
