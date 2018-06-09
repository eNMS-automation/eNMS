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
  if ($('#' + dates[i]).length) {
    $('#' + dates[i]).data("DateTimePicker").minDate(today);
  }
}

function openWizard(){
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