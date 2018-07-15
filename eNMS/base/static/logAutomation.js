table = $('#table').DataTable();

function addLogRule(properties) {
  values = [];
  for (var i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(`<button type="button" class="btn btn-danger btn-xs" onclick="editLogRule('${properties.id}')">Delete</button>`);
  values.push(`<button type="button" class="btn btn-danger btn-xs" onclick="deleteLogRule('${properties.id}')">Delete</button>`);
  var rowNode = table.row.add(values).draw(false).node();
  $(rowNode).attr("id", `${properties.id}`);
}

(function() {
  for (var i = 0; i < logRules.length; i++) {
    addLogRule(logRules[i]);
  }
})();

function saveRule() {
  $.ajax({
    type: "POST",
    url: '/create_log_rule',
    data: $('#log-automation-form').serialize(),
    success: function(logRule) {
      addLogRule(logRule);
      alertify.notify(`Log rule created !`, 'success', 5);
    }
  });
}

function deleteLogRule(id) {
  $.ajax({
    type: "POST",
    url: `/delete_log_rule/${id}`,
    success: function() {
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify("Log rule deleted", 'error', 5);
    }
  });
}