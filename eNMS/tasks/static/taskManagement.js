var taskId = null;
var table = $('#table').DataTable();

function addTask(mode, properties) {
  values = [];
  for (var i = 0; i < fields.length; i++) {
    if (fields[i] != 'recurrent') {
      values.push(`${properties[fields[i]]}`);
    }
  }
  var status = properties.status == "active" ? 'pause' : 'resume';
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTaskLogs('${properties.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="compareTaskLogs('${properties.id}')"></i>Compare</a></button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="showTaskModal('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runTask('${properties.id}')">Run</button>`,
    `<button id="pause-resume-${properties.id}" type="button"
    class="btn btn-danger btn-xs" onclick="${status}Task('${properties.id}')">
    ${status.charAt(0).toUpperCase() + status.substr(1)}</button>`,   
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteTask('${properties.id}')">Delete</button>`
  );

  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    var rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr("id", `${properties.id}`);
  }
}

(function() {
  if (typeof tasks !== 'undefined') {
    for (var i = 0; i < tasks.length; i++) {
      addTask('create', tasks[i]);
    }
  }
})();

function scheduleTask() {
  if ($("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/tasks/scheduler",
      dataType: "json",
      data: $("#scheduling-form").serialize(),
      success: function(result) {
        alertify.notify(`Task '${result.name}' edited.`, 'success', 5);
      }
    });
    $("#scheduling").modal('hide');
  } else {
    alertify.notify('Some fields are missing', 'error', 5);
  }
}