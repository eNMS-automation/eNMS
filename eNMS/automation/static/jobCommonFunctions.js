/*
global
alertify: false
call: false
diffview: false
*/

let jobId;

/**
 * Show the logs modal for a job.
 * @param {id} id - Job id.
 */
function showLogs(id) { // eslint-disable-line no-unused-vars
  jobId = id;
  call(`/automation/show_logs/${id}`, function(logs) {
    $('#logs').text(logs.replace(/\\n/g, '\n'));
    $(`#show-logs-modal`).modal('show');
  });
}

/**
 * Clear the logs
 * @param {id} id - Job id.
 */
function clearLogs() { // eslint-disable-line no-unused-vars
  call(`/automation/clear_logs/${jobId}`, () => {
    $('#logs').empty();
    alertify.notify(`Logs cleared`, 'success', 5);
  });
}

/**
 * Show the compare logs modal for job.
 * @param {id} id - Job id.
 */
function compareLogs(id) { // eslint-disable-line no-unused-vars
  jobId = id;
  call(`/automation/compare_logs/${id}`, function(results) {
    $('#first_version,#second_version').empty();
    for (let i = 0; i < results.versions.length; i++) {
      const value = results.versions[i];
      $('#first_version,#second_version').append($('<option></option>')
        .attr('value', value).text(value));
    }
    $('#logs-modal').modal('show');
  });
}

$('#first_version,#second_version').on('change', function() {
  $('#view').empty();
  const v1 = $('#first_version').val();
  const v2 = $('#second_version').val();
  call(`/automation/get_diff/${jobId}/${v1}/${v2}`, function(data) {
    $('#view').append(diffview.buildView({
      baseTextLines: data.first,
      newTextLines: data.second,
      opcodes: data.opcodes,
      baseTextName: `${v1}`,
      newTextName: `${v2}`,
      contextSize: null,
      viewType: 0,
    }));
  });
});

/**
 * Run job.
 * @param {id} id - Job id.
 */
function runJob(id) { // eslint-disable-line no-unused-vars
  call(`/automation/run_job/${id}`, function(job) {
    alertify.notify(`Job '${job.name}' started.`, 'success', 5);
  });
}
