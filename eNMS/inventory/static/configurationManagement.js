/*
global
addInstance: false
devices: false
doc: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Table Actions.
 * @param {values} values - values array.
 * @param {device} device - Device properties.
 */
function tableActions(values, device) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="configurationModal('${device.id}')">Configuration</button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="connectionParametersModal('${device.id}')">Connect</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('device', '${device.id}')">Edit</button>`
  );
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

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  for (let i = 0; i < devices.length; i++) {
    addInstance('create', 'device', devices[i]);
  }
})();
