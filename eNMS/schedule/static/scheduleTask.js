/*
global
alertify: false
*/

const dates = ['start_date', 'end_date'];
const today = new Date();
for (let i = 0; i < dates.length; i++) {
  $('#task_' + dates[i]).datetimepicker({
    format: 'DD/MM/YYYY HH:mm:ss',
    widgetPositioning: {
      horizontal: 'left',
      vertical: 'bottom',
    },
    useCurrent: false,
  });
  if ($('#task_' + dates[i]).length) {
    $('#task_' + dates[i]).data('DateTimePicker').minDate(today);
  }
}

/**
 * Schedule a task.
 */
function scheduleTask() {
  if ($('#scheduling-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/schedule/scheduler',
      dataType: 'json',
      data: $('#scheduling-form').serialize(),
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          $('#scheduling').modal('hide');
          alertify.notify(`Task '${result.name}' scheduled.`, 'success', 5);
        }
      },
    });
  } else {
    alertify.notify('Some fields are missing.', 'error', 5);
  }
}
