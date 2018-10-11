/**
 * Show the task modal for task.
 * @param {id} id - Task id.
 */
function showTaskModal(id) { // eslint-disable-line no-unused-vars
  if (!id) {
    $('#title').text('Create a new task');
    $('#task-modal-form').trigger('reset');
    $('#task-modal').modal('show');
  } else {
    $.ajax({
      type: 'POST',
      url: `/schedule/get/${id}`,
      dataType: 'json',
      success: function(properties) {
        console.log(properties);
        if (!properties) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          for (const [property, value] of Object.entries(properties)) {
            $(`#${property}`).val(value);
          }
          $('#job').val(properties.job.id);
        }
        $('#title').text(`Edit task '${properties.name}'`);
      },
    });
  }
  $('#task-modal').modal('show');
}
