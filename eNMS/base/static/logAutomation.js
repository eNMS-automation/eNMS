/*
global
alertify: false
*/

table = $('#table').DataTable();

function addLogRule(properties, mode) {
  let values = [];
  for (var i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(`<button type="button" class="btn btn-info btn-xs"
  onclick="showLogRuleModal('${properties.id}')">Edit</button>`);
  values.push(`<button type="button" class="btn btn-danger btn-xs"
  onclick="deleteLogRule('${properties.id}')">Delete</button>`);

  if (mode == 'edited') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    var rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr("id", `${properties.id}`);
  }
}

(function() {
  for (var i = 0; i < logRules.length; i++) {
    addLogRule(logRules[i], 'create');
  }
})();

function showModal() { // eslint-disable-line no-unused-vars
  $("#title").text("Add a new log rule");
  $("#edit-form").trigger("reset");
  $("#edit").modal("show");
}

function showLogRuleModal(id) { // eslint-disable-line no-unused-vars
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

function saveRule() { // eslint-disable-line no-unused-vars
  $.ajax({
    type: "POST",
    url: '/save_log_rule',
    data: $('#edit-form').serialize(),
    success: function(logRule) {
      var mode = $('#title').text().startsWith('Edit') ? 'edited' : 'created';
      addLogRule(logRule, mode);
      alertify.notify(`Log rule '${logRule.name}' ${mode}.`, 'success', 5);
      $("#edit").modal('hide');
    }
  });
}

function deleteLogRule(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: "POST",
    url: `/delete_log_rule/${id}`,
    success: function() {
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify("Log rule successfully deleted.", 'error', 5);
    }
  });
}