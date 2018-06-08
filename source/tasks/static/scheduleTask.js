var dates = ['start_date', 'end_date'];
var today = new Date();
for (var i = 0; i < dates.length; i++) {
  $('#' + dates[i]).datetimepicker({
    format: 'DD/MM/YYYY HH:mm:ss',
    widgetPositioning: {
      horizontal: 'left',
      vertical: 'bottom'
    },
    useCurrent: false,
  });
  $('#' + dates[i]).data("DateTimePicker").minDate(today);
}

function schedule(){
  $('#wizard').smartWizard({
    onFinish: scheduleTask,
    enableFinishButton: true,
  });
  $('.buttonNext').addClass('btn btn-success');
  $('.buttonPrevious').addClass('btn btn-primary');
  $('.buttonFinish').addClass('btn btn-default');
}

// when a filter is selected, apply it
$('#script_type').on('change', function() {
  $.ajax({
    type: "POST",
    url: `/scripts/script_type_${this.value}`,
    dataType: "json",
    success: function(scripts){
      $("#scripts").empty();
      $.each(scripts, function(_, s) {
        $("#scripts").append(`<option value="${s.id}">${s.name}</option>`);
      });
    }
  });
});

function scheduleTask() {
  if ($("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: `/tasks/scheduler`,
      dataType: "json",
      data: $("#scheduling-form").serialize(),
      success: function() {
      alertify.notify('Task scheduled', 'success', 5);
      }
    });
    $("#scheduling").modal('hide');
  } else {
    alertify.notify('Some fields are missing', 'error', 5);
  }
}