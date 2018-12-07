/*
global
alertify: false
call: false
diffview: false
getJobState: false
getWorkflowState: false
partial
table: false
*/

let jobId;
let refresh;

$('#logs-modal').on('hidden.bs.modal', function() {
  refresh = false;
});

/**
 * Open smart wizard.
 * @param {type} type - Service or Workflow.
 */
function openWizard(type) { // eslint-disable-line no-unused-vars
  $(`#${type}-wizard`).smartWizard({
    enableAllSteps: true,
  });
  $('.buttonNext').addClass('btn btn-success');
  $('.buttonPrevious').addClass('btn btn-primary');
  $('.buttonFinish').hide();
}

/**
 * Display logs.
 */
function displayLogs() { // eslint-disable-line no-unused-vars
  call(`/automation/get_logs/${jobId}`, (logs) => {
    $('#display,#compare_with').empty();
    const times = Object.keys(logs);
    times.forEach((option) => {
      $('#display,#compare_with').append(
        $('<option></option>').attr('value', option).text(option)
      );
    });
    $('#display,#compare_with').val(times[times.length - 1]);
    const firstLogs = logs[$('#display').val()];
    if (firstLogs) {
      $('#logs').text(
        JSON.stringify(firstLogs, null, 2).replace(
          /(?:\\[rn]|[\r\n]+)+/g, '\n'
        )
      );
    }
  });
}

/**
 * Display logs.
 * @param {firstTime} firstTime - First time.
 */
function refreshLogs(firstTime=false) { // eslint-disable-line no-unused-vars
  if (firstTime) {
    refresh = !refresh;
    $('#refresh-logs-button').text(
      refresh ? 'Stop periodic Refresh' : 'Trigger periodic Refresh'
    );
  }
  if (refresh) {
    displayLogs();
    setTimeout(refreshLogs, 5000);
  }
}

/**
 * Show the logs modal for a job.
 * @param {id} id - Job id.
 */
function showLogs(id) { // eslint-disable-line no-unused-vars
  jobId = id;
  $('#logs').empty();
  displayLogs();
  $('#logs-modal').modal('show');
}

/**
 * Clear the logs
 * @param {id} id - Job id.
 */
function clearLogs() { // eslint-disable-line no-unused-vars
  call(`/automation/clear_logs/${jobId}`, () => {
    $('#logs').empty();
    alertify.notify('Logs cleared.', 'success', 5);
    $('#logs-modal').modal('hide');
  });
}

/**
 * Detach window
 */
function detachWindow() { // eslint-disable-line no-unused-vars
  window.open(
    `/automation/detach_logs/${jobId}`,
    'Logs',
    'height=800,width=600'
  ).focus();
  $('#logs-modal').modal('hide');
}

$('#display').on('change', function() {
  call(`/automation/get_logs/${jobId}`, (logs) => {
    const log = logs[$('#display').val()];
    $('#logs').text(
      JSON.stringify(log, null, 2).replace(/(?:\\[rn]|[\r\n]+)+/g, '\n')
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
    alertify.notify(`Job '${job.name}' started.`, 'success', 5);
    if (typeof workflowBuilder !== 'undefined') {
      if (job.type == 'Workflow') {
        getWorkflowState();
      } else {
        getJobState(id);
      }
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
    setTimeout(partial(getStatus, type), 5000);
  });
}
