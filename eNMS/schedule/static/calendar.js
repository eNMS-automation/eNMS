/*
global
tasks: false
*/

$(function() {
  if (typeof ($.fn.fullCalendar) === 'undefined') {
    return;
  }
  let events = [];
  for (const [name, properties] of Object.entries(tasks)) {
    console.log(tasks);
    events.push({
      title: name,
      taskId: properties.id,
      description: properties.description,
      start: new Date(...properties.date),
    });
  }
  $('#calendar').fullCalendar({
    header: {
      left: 'prev,next today',
      center: 'title',
      right: 'month,agendaWeek,agendaDay,listMonth',
    },
    selectable: true,
    selectHelper: true,
    eventClick: function(calEvent, jsEvent, view) {
      console.log(calEvent);
      $.ajax({
        type: 'POST',
        url: `/schedule/get/${calEvent.taskId}`,
        dataType: 'json',
        success: function(result){
          if (!result) {
            alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
          } else {
            for (const [property, value] of Object.entries(result)) {
              $(`#${property}`).val(value);
            }
          }
        }
      });
      $('#task-modal').modal('show');
    },
    editable: true,
    events: events,
  });
});
