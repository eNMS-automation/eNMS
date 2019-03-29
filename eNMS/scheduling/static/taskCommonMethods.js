/*
global
convertSelect: false
doc: false
*/

(function() {
  convertSelect("#task-job");
  const dates = ["task-start_date", "task-end_date"];
  const today = new Date();
  for (let i = 0; i < dates.length; i++) {
    $("#" + dates[i]).datetimepicker({
      format: "DD/MM/YYYY HH:mm:ss",
      widgetPositioning: {
        horizontal: "left",
        vertical: "bottom",
      },
      useCurrent: false,
    });
    if ($(`#${dates[i]}`).length) {
      $(`#${dates[i]}`)
        .data("DateTimePicker")
        .minDate(today);
    }
  }
  doc("https://enms.readthedocs.io/en/latest/scheduling/task_management.html");
})();
