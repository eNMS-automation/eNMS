/*
global
call: false
*/

/**
 * Show the task modal for task.
 * @param {id} id - Task id.
 * @param {duplicate} duplicate - Duplicate.
 */
function showTaskModal(id, duplicate) { // eslint-disable-line no-unused-vars
  if (!id) {
    $('#title').text('Create a New Task');
    $('#task-modal-form').trigger('reset');
    $('#task-modal').modal('show');
  } else {
    call(`/get/task/${id}`, function(task) {
      $('#title').text(
        `${duplicate ? 'Duplicate' : 'Edit'} Task '${task.name}'`
      );
      if (duplicate) {
        task.id = task.name = '';
      }
      for (const [property, value] of Object.entries(task)) {
        $(`#${property}`).val(value);
      }
      $('#job').val(task.job.id);
    });
  }
  $('#task-modal').modal('show');
}
