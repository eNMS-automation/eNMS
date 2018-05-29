$(function() {
  if( typeof ($.fn.fullCalendar) === 'undefined'){ return; }

  var date = new Date(),
    d = date.getDate(),
    m = date.getMonth(),
    y = date.getFullYear(),
    started,
    categoryClass;

  var events = []
  for (const [name, properties] of Object.entries(tasks)) {
    events.push({
      title: name,
      description: properties.description,
      start: new Date(...properties.date)
    });
  }

  var calendar = $('#calendar').fullCalendar({
    header: {
    left: 'prev,next today',
    center: 'title',
    right: 'month,agendaWeek,agendaDay,listMonth'
    },
    selectable: true,
    selectHelper: true,
    eventClick: function(calEvent, jsEvent, view) {
      $.ajax({
        type: "POST",
        url: `/tasks/get/${calEvent.title}`,
        dataType: 'json',
        success: function(properties){
          for (const [property, value] of Object.entries(properties)) {
            $(`#${property}`).val(value);
          }
        }
      });
      $('#scheduling').modal('show');
    },
    editable: true,
    events: events
  });
});