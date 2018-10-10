/*
global
alertify: false
*/

(function() {
  $('#start_date,#end_date,#frequency').attr('disabled', true);
  $('#run-now,#do-not-run').change(function() {
    $('#start_date,#end_date,#frequency').attr('disabled', true);
  });
  $('#schedule').change(function() {
    $('#start_date,#end_date,#frequency').attr('disabled', false);
  });
})();

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

// when a filter is selected, apply it
$('#service_type').on('change', function() {
  $.ajax({
    type: 'POST',
    url: `/services/service_type/${this.value}`,
    dataType: 'json',
    success: function(services) {
      if (!services) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        $('#service').empty();
        $.each(services, function(_, s) {
          $('#service').append(`<option value="${s.id}">${s.name}</option>`);
        });
      }
    },
  });
});

/**
 * Schedule a task.
 */
function scheduleTask() {
  if ($('#scheduling-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/tasks/scheduler',
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
