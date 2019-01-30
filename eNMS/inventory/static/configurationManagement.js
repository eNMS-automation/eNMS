/*
global
alertify: false
call: false
convertSelect: false
diffview: false
doc: false
fCall: false
initTable: false
refreshTable: false
*/

let table = initTable( // eslint-disable-line no-unused-vars
  'device', 'configuration', ['Download']
);
let deviceId;

/**
 * Display configurations.
 */
function displayConfigurations() { // eslint-disable-line no-unused-vars
  call(`/inventory/get_configurations/${deviceId}`, (configurations) => {
    $('#display,#compare_with').empty();
    const times = Object.keys(configurations);
    times.forEach((option) => {
      $('#display,#compare_with').append(
        $('<option></option>').attr('value', option).text(option)
      );
    });
    $('#display,#compare_with').val(times[times.length - 1]);
    const firstConfigurations = configurations[$('#display').val()];
    if (firstConfigurations) {
      $('#configurations').text(
        JSON.stringify(firstConfigurations, null, 2).replace(
          /(?:\\[rn]|[\r\n]+)+/g, '\n'
        )
      );
    }
  });
}

/**
 * Configure poller.
 */
function configurePoller() { // eslint-disable-line no-unused-vars
  fCall('/inventory/configure_poller', '#configure-poller-form', function() {
    alertify.notify('Poller started.', 'success', 5);
    $('#poller-modal').modal('hide');
  });
}

/**
 * Search in all Configurations.
 */
function searchConfigurations() { // eslint-disable-line no-unused-vars
  fCall(
    '/inventory/search_configurations',
    '#search-configurations-form',
    function(devices) {
      alertify.notify('Configurations filtered.', 'success', 5);
      $('#search-configurations-modal').modal('hide');
    }
  );
}

/**
 * Show the configurations modal for a job.
 * @param {id} id - Job id.
 */
function showConfigurations(id) { // eslint-disable-line no-unused-vars
  deviceId = id;
  $('#configurations').empty();
  displayConfigurations();
  $('#configurations-modal').modal('show');
}

/**
 * Clear the configurations
 */
function clearConfigurations() { // eslint-disable-line no-unused-vars
  call(`/inventory/clear_configurations/${deviceId}`, () => {
    $('#configurations').empty();
    alertify.notify('Configurations cleared.', 'success', 5);
    $('#configurations-modal').modal('hide');
  });
}

$('#display').on('change', function() {
  call(`/inventory/get_configurations/${deviceId}`, (configurations) => {
    const log = configurations[$('#display').val()];
    $('#configurations').text(
      JSON.stringify(log, null, 2).replace(/(?:\\[rn]|[\r\n]+)+/g, '\n')
    );
  });
});

$('#compare_with').on('change', function() {
  $('#configurations').empty();
  const v1 = $('#display').val();
  const v2 = $('#compare_with').val();
  call(`/inventory/get_diff/${deviceId}/${v1}/${v2}`, function(data) {
    $('#configurations').append(diffview.buildView({
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
 * Show Raw Logs.
 * @param {deviceId} deviceId - Device ID.
 */
function showRawLogs() { // eslint-disable-line no-unused-vars
  window.open(
    `/inventory/get_raw_logs/${deviceId}/${$('#display').val()}`,
    'Configuration',
    'height=800,width=600'
  ).focus();
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  convertSelect('#pools', '#devices');
  refreshTable(5000);
})();
