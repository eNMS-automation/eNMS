/**
 * Server-side table filtering.
 */
// eslint-disable-next-line
function filter() {
  table.ajax.reload(null, false);
  alertify.notify("Filter applied.", "success", 5);
}

/**
 * Datatable periodic refresh.
 * @param {interval} interval - Refresh interval.
 */
// eslint-disable-next-line
function refreshTable(interval) {
  table.ajax.reload(null, false);
  setTimeout(() => refreshTable(interval), 5000);
}