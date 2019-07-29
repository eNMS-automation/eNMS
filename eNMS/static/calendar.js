/*
global
call: false
showTypePanel: false
*/

console.log();

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
        start: new Date(...properties.date),
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
      eventClick: function(calEvent, jsEvent, view) {
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
