table = $('#table').DataTable();

function addLogRule(properties) {
    console.log(properties);
  values = [];
  for (var i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(`<button type="button" class="btn btn-info btn-xs" onclick="showLogRuleModal('${properties.id}')">Edit</button>`);
  values.push(`<button type="button" class="btn btn-danger btn-xs" onclick="deleteLogRule('${properties.id}')">Delete</button>`);
  var rowNode = table.row.add(values).draw(false).node();
  $(rowNode).attr("id", `${properties.id}`);
}

(function() {
  for (var i = 0; i < logRules.length; i++) {
    addLogRule(logRules[i]);
  }
})();

function showModal() {
  $("#title").text("Add a new log rule");
  $("#edit-form").trigger("reset");
  $("#edit").modal("show");
}

function showLogRuleModal(id) {
  $.ajax({
    type: "POST",
    url: `/get_log_rule/${id}`,
    success: function(logRule){
      for (const [property, value] of Object.entries(logRule)) {
        if (property.includes("regex")) {
          $(`#${property}`).prop('checked', value);
        } else {
          $(`#${property}`).val(value);
        }
        $('#title').text(`Edit log rule properties`);
      }
    }
  });
  $("#edit").modal('show');
}

function saveRule() {
  $.ajax({
    type: "POST",
    url: '/create_log_rule',
    data: $('#edit-form').serialize(),
    success: function(logRule) {
      addLogRule(logRule);
      alertify.notify(`Log rule '${logRule.name}' created !`, 'success', 5);
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