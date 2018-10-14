/*
global
alertify: false
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
    $.ajax({
      type: 'POST',
      url: `/scheduling/get/${id}`,
      dataType: 'json',
      success: function(properties) {
        if (!properties) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          for (const [property, value] of Object.entries(properties)) {
            $(`#${property}`).val(value);
          }
          $('#job').val(properties.job.id);
        }
        $('#title').text(`Edit Task '${properties.name}'`);
      },
    });
  }
  $('#task-modal').modal('show');
}
