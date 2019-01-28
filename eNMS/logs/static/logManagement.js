/*
global
alertify: false
fCall: false
fields: false
logs: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

(function() {
  for (let i = 0; i < logs.length; i++) {
    addLog(logs[i]);
  }
})();

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
