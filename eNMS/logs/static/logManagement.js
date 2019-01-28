/*
global
alertify: false
fCall: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Filter logs.
 */
function filterLogs() { // eslint-disable-line no-unused-vars
  fCall('/logs/filter_logs', '#filtering-form', function(logs) {
    table.clear().draw();
    for (let i = 0; i < logs.length; i++) {
      addLog(logs[i]);
    }
    alertify.notify(`Logs successfully filtered.`, 'success', 5);
  });
}

(function() {

})();

