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
    events.push({
      title: name,
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
      /*
      $.ajax({
        type: 'POST',
        url: `/tasks/get/${calEvent.title}`,
        dataType: 'json',
        success: function(properties){
          for (const [property, value] of Object.entries(properties)) {
            $(`#${property}`).val(value);
          }
        }
      });
      $('#scheduling').modal('show');
      */
    },
    editable: true,
    events: events,
  });
});
