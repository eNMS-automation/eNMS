/**
 * Datatable per-column search.
 * @param {cls} cls - Object class.
 * @param {type} type - Table type.
 * @return {table}
 */
// eslint-disable-next-line
function initTable(type) {
  // eslint-disable-next-line new-cap
  const table = $("#table").DataTable({
    serverSide: true,
    orderCellsTop: true,
    scrollX: true,
    sDom: "<'top'i>rt<'bottom'lp><'clear'>",
    ajax: {
      url: `/filtering/table/${type}`,
      data: (d) => {
        d.form = serializeForm(`#${type}_filtering-form`);
      }
    },
  });
  return table;
}

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