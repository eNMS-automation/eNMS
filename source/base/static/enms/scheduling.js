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
    onFinish: scheduleScript,
    enableFinishButton: true,
  });
  $('.buttonNext').addClass('btn btn-success');
  $('.buttonPrevious').addClass('btn btn-primary');
  $('.buttonFinish').addClass('btn btn-default');
  $('#wizard').smartWizard('enableFinish', true);
}