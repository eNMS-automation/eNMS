/*
global
alertify: false
diffview: false
*/

let taskId;

/**
 * Show the logs modal for a task.
 * @param {id} id - Task id.
 */
function showLogs(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/services/show_logs/${id}`,
    dataType: 'json',
    success: function(logs) {
      if (!logs) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        $('#logs').text(logs);
      }
    },
  });
  $(`#show-logs-modal`).modal('show');
}

/**
 * Show the compare logs modal for task.
 * @param {id} id - Task id.
 */
function compareLogs(id) { // eslint-disable-line no-unused-vars
  taskId = id;
  $.ajax({
    type: 'POST',
    url: `/services/compare_logs/${id}`,
    dataType: 'json',
    success: function(results) {
      if (!results) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        $('#first_version,#second_version').empty();
        for (let i = 0; i < results.versions.length; i++) {
          const value = results.versions[i];
          $('#first_version,#second_version').append($('<option></option>')
            .attr('value', value).text(value));
        }
      }
    },
  });
  $('#logs-modal').modal('show');
}

$('#first_version,#second_version').on('change', function() {
  $('#view').empty();
  const v1 = $('#first_version').val();
  const v2 = $('#second_version').val();
  $.ajax({
    type: 'POST',
    url: `/services/get_diff/${taskId}/${v1}/${v2}`,
    dataType: 'json',
    success: function(data) {
      $('#view').append(diffview.buildView({
        baseTextLines: data.first,
        newTextLines: data.second,
        opcodes: data.opcodes,
        baseTextName: `${v1}`,
        newTextName: `${v2}`,
        contextSize: null,
        viewType: 0,
      }));
    },
  });
});
