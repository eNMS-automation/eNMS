/*
global
alertify: false
fCall: false
fields: false
logs: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add log to datatable.
 * @param {properties} properties - Properties of the log.
 */
function addLog(properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(`<button type="button" class="btn btn-danger btn-xs"
  onclick="deleteInstance('Log', '${properties.id}')">Delete</button>`);
  const rowNode = table.row.add(values).draw(false).node();
  $(rowNode).attr('id', `${properties.id}`);
}

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
