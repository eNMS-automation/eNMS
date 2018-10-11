/*
global
alertify: false
*/

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

/**
 * Schedule a task.
 */
function scheduleTask() {
  if ($('#task-modal-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/schedule/scheduler',
      dataType: 'json',
      data: $('#task-modal-form').serialize(),
      success: function(result) {
        console.log(taskManagement);
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          $('#task-modal').modal('hide');
          addTask(mode, properties)
          alertify.notify(`Task '${result.name}' scheduled.`, 'success', 5);
        }
      },
    });
  } else {
    alertify.notify('Some fields are missing.', 'error', 5);
  }
}
