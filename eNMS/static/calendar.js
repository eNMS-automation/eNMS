/*
global
showTypePanel: false
tasks: false
*/

const taskManagement = false; // eslint-disable-line no-unused-vars

$(function() {
  if (typeof $.fn.fullCalendar === "undefined") {
    return;
  }
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
      showTypePanel("task", calEvent.id);
    },
    editable: true,
    events: events,
  });
});
