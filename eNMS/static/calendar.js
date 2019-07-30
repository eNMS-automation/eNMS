/*
global
call: false
showTypePanel: false
*/

$(function() {
  if (typeof $.fn.fullCalendar === "undefined") {
    return;
  }
  call(`/calendar_init/${calendarType}`, function(tasks) {
    let events = [];
    for (const [name, properties] of Object.entries(tasks)) {
      events.push({
        title: name,
        id: properties.id,
        description: properties.description,
        start: new Date(...properties.start),
        end: new Date(...properties.end),
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
      eventClick: function(calEvent) {
        if (calendarType == "task") {
          showTypePanel("task", calEvent.id);
        } else {
          showResultsPanel(calEvent.id, calEvent.title, 'run');
        }
      },
      editable: true,
      events: events,
    });
  });
});
