/*
global
call: false
convertSelect: false
*/

(function() {
  convertSelect('#job');
  if (taskManagement) {
    for (let i = 0; i < tasks.length; i++) {
      addTask('create', tasks[i]);
    }
    getStatus();
  }
  const dates = ['start_date', 'end_date'];
  const today = new Date();
  for (let i = 0; i < dates.length; i++) {
    $('#' + dates[i]).datetimepicker({
      format: 'DD/MM/YYYY HH:mm:ss',
      widgetPositioning: {
        horizontal: 'left',
        vertical: 'bottom',
      },
      useCurrent: false,
    });
    if ($('#' + dates[i]).length) {
      $('#' + dates[i]).data('DateTimePicker').minDate(today);
    }
  }
  doc('https://enms.readthedocs.io/en/latest/scheduling/task_management.html');
})();

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
