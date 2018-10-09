/*
global
alertify: false
diffview: false
table: false
*/

let taskId;

/**
 * Show the logs modal for a task.
 * @param {id} id - Task id.
 */
function showLogs(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/tasks/show_logs/${id}`,
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
    url: `/tasks/compare_logs/${id}`,
    dataType: 'json',
    success: function(results) {
      if (!results) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        $('#first_version,#second_version').empty();
        $('#first_device,#second_device').empty();
        for (let i = 0; i < results.versions.length; i++) {
          const value = results.versions[i];
          $('#first_version,#second_version').append($('<option></option>')
            .attr('value', value).text(value));
        }
        for (let i = 0; i < results.devices.length; i++) {
          const value = results.devices[i];
          $('#first_device,#second_device').append($('<option></option>')
            .attr('value', value).text(value));
        }
      }
    },
  });
  $('#logs-modal').modal('show');
}

const dropDowns = '#first_version,#second_version,#first_device,#second_device';
$(dropDowns).on('change', function() {
  $('#view').empty();
  const v1 = $('#first_version').val();
  const v2 = $('#second_version').val();
  const n1 = $('#first_device').val();
  const n2 = $('#second_device').val();
  const nodeSlugs = n1 && n2 ? `/${n1}/${n2}` : '';
  $.ajax({
    type: 'POST',
    url: `/tasks/get_diff/${taskId}/${v1}/${v2}${nodeSlugs}`,
    dataType: 'json',
    success: function(data) {
      $('#view').append(diffview.buildView({
        baseTextLines: data.first,
        newTextLines: data.second,
        opcodes: data.opcodes,
        baseTextName: `${n1} - ${v1}`,
        newTextName: `${n2} - ${v2}`,
        contextSize: null,
        viewType: 0,
      }));
    },
  });
});
