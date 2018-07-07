table = $('#log-table').DataTable();

function addLog(properties) {
  values = [];
  for (var i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(`<button type="button" class="btn btn-danger btn-xs" onclick="deleteLog('${properties.id}')">Delete</button>`);
  var rowNode = table.row.add(values).draw(false).node();
  $(rowNode).attr("id", `${properties.id}`);
}

(function() {
  for (var i = 0; i < logs.length; i++) {
    addLog(logs[i]);
  }
})();

function filterLogs() {
  $.ajax({
    type: "POST",
    url: "/filter_logs",
    data: $('#filtering-form').serialize(),
    success: function(logs) {
      table.clear().draw();;
      for (var i = 0; i < logs.length; i++) {
        addLog(logs[i]);
      }
      alertify.notify(`Logs successfully filtered !`, 'success', 5);
    }
  });
}

function deleteLog(id) {
  $.ajax({
    type: "POST",
    url: `/delete_log/${id}`,
    success: function() {
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify("Log deleted", 'error', 5);
    }
  });
}