/*
global
alertify: false
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
  onclick="deleteLog('${properties.id}')">Delete</button>`);
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
  $.ajax({
    type: 'POST',
    url: '/logs/filter_logs',
    data: $('#filtering-form').serialize(),
    success: function(logs) {
      table.clear().draw();
      for (let i = 0; i < logs.length; i++) {
        addLog(logs[i]);
      }
      alertify.notify(`Logs successfully filtered.`, 'success', 5);
    },
  });
}

/**
 * Delete log.
 * @param {id} id - Id of the log to be deleted.
 */
function deleteLog(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/logs/delete_log/${id}`,
    success: function(result) {
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        table.row($(`#${id}`)).remove().draw(false);
        alertify.notify('Log successfully deleted.', 'error', 5);
      }
    },
  });
}
