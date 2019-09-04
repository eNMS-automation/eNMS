/*
global
calendarType: false
call: false
showResultsPanel: false
showTypePanel: false
*/

$(function() {
  if (typeof $.fn.fullCalendar === "undefined") {
    return;
  }
  call(`/calendar_init/${calendarType}`, function(tasks) {
    let events = [];
    for (const [name, properties] of Object.entries(tasks)) {
      if (properties.job === undefined) continue;
      events.push({
        title: name,
        id: properties.id,
        description: properties.description,
        start: new Date(...properties.start),
        runtime: properties.runtime,
        jobId: properties.job.id,
        jobType: properties.job.type == "Workflow" ? "workflow" : "service",
      });
    }
    $("#calendar").fullCalendar({
      header: {
        left: "prev,next today",
        center: "title",
        right: "month,agendaWeek,agendaDay,listMonth",
      },
      selectable: true,
      selectHelper: true,
      eventClick: function(e) {
        if (calendarType == "task") {
          showTypePanel("task", e.id);
        } else {
          showResultsPanel(e.jobId, e.title, e.runtime);
        }
      },
      editable: true,
      events: events,
    });
  });
});
