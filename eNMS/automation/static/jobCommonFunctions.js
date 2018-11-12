/*
global
alertify: false
call: false
diffview: false
partial
table: false
*/

let jobId;

/**
 * Show the logs modal for a job.
 * @param {id} id - Job id.
 */
function showLogs(id) { // eslint-disable-line no-unused-vars
  jobId = id;
  call(`/get/job/${id}`, (job) => {
    $('#display,#compare_with').empty();
    Object.keys(job.logs).forEach((option) => {
      $('#display,#compare_with').append(
        $('<option></option>').attr('value', option).text(option)
      );
    });
    const logs = job.logs[$('#display').val()];
    if (logs) {
      $('#logs').text(
        JSON.stringify(logs, null, 2).replace(/(?:\\[rn]|[\r\n]+)+/g, '\n')
      );
      $('#logs-modal').modal('show');
    } else {
      alertify.notify('Logs are empty.', 'error', 5);
    }
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
    $(`#show-logs-modal`).modal('hide');
  });
}

$('#display').on('change', function() {
  call(`/get/job/${jobId}`, (job) => {
    const logs = job.logs[$('#display').val()];
    $('#logs').text(
      JSON.stringify(logs, null, 2).replace(/(?:\\[rn]|[\r\n]+)+/g, '\n')
    );
  });
});

$('#compare_with').on('change', function() {
  $('#logs').empty();
  const v1 = $('#display').val();
  const v2 = $('#compare_with').val();
  call(`/automation/get_diff/${jobId}/${v1}/${v2}`, function(data) {
    $('#logs').append(diffview.buildView({
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
    if (job.error) {
      alertify.notify(job.error, 'error', 5);
    } else {
      alertify.notify(`Job '${job.name}' started.`, 'success', 5);
    }
  });
}

/**
 * Get Service Status.
 * @param {type} type - Service or Workflow.
 */
function getStatus(type) { // eslint-disable-line no-unused-vars
  call(`/automation/get_status/${type}`, function(status) {
    for (let i = 0; i < status.length; i++) {
      const col = table.column('#status');
      table.cell(i, col).data(status[i]).draw(false);
    }
    setTimeout(partial(getStatus, type), 1000);
  });
}
