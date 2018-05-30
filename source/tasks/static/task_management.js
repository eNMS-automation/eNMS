(function() {
  var taskId = null;
  var table = $('#table').DataTable();

  for (i = 0; i < tasks.length; i++) {
    addTask('create', tasks[i]);
  }
})();

function addTask(mode, properties) {
  values = [];
  for (j = 0; j < fields.length; j++) {
    values.push(`${properties[fields[j]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs" onclick="showTaskLogs('${properties.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-info btn-xs" onclick="compareTaskLogs('${properties.id}')"></i>Compare</a></button>`,
    `<button type="button" class="btn btn-info btn-xs" onclick="showTaskModal('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs" onclick="deleteTask('${properties.id}')">Delete</button>`
  );
  if (properties.frequency) {
    if (properties.status == "active") {
      values.push(`<button id="pause-resume-{{ task.id }}" type="button" class="btn btn-danger btn-xs" onclick="pauseTask('${properties.id}')">Pause</button>`)
    } else {
    values.push(`<button id="pause-resume-{{ task.id }}" type="button" class="btn btn-danger btn-xs" onclick="resumeTask('${properties.id}')">Resume</button>`)
    }
  }
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    var rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr("id", `${properties.id}`);
  }
}

function showTaskModal(id) {
  taskId = id;
  $.ajax({
    type: "POST",
    url: `/tasks/get/${id}`,
    dataType: 'json',
    success: function(properties){
      for (const [property, value] of Object.entries(properties)) {
        $(`#${property}`).val(value);
      }
    }
  });
  $('#scheduling').modal('show');
}

function scheduleScript() {
  if ($("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/tasks/view_scheduler",
      dataType: "json",
      data: $("#scheduling-form").serialize(),
      success: function() {
        alertify.notify('Task edited', 'success', 5);
      }
    });
    $("#scheduling").modal('hide');
  }
}

function showTaskLogs(id) {
  $.ajax({
    type: "POST",
    url: `/tasks/show_logs/${id}`,
    dataType: 'json',
    success: function(logs){
      $("#logs").text(logs);
    }
  });
  $(`#show-logs-modal`).modal('show');
}

function compareTaskLogs(id) {
  taskId = id;
  $.ajax({
    type: "POST",
    url: `/tasks/compare_logs/${id}`,
    dataType: 'json',
    success: function(results){
      $("#first_version,#second_version,#first_node,#second_node,#first_script,#second_script").empty();
      for (i = 0; i < results.versions.length; i++) {
        value = results.versions[i];
        $("#first_version,#second_version").append($("<option></option>")
          .attr("value", value).text(value));
      }
      for (i = 0; i < results.nodes.length; i++) {
        value = results.nodes[i];
        $("#first_node,#second_node").append($("<option></option>")
          .attr("value", value).text(value));
      }
      for (i = 0; i < results.scripts.length; i++) {
        value = results.scripts[i];
        $("#first_script,#second_script").append($("<option></option>")
          .attr("value", value).text(value));
      }
    }
  });
  $('#compare-logs-modal').modal('show');
}

$("#first_version,#second_version,#first_node,#second_node,#first_script,#second_script").on('change', function() {
  $("#view").empty();
  var v1 = $("#first_version").val()
      v2 = $("#second_version").val()
      n1 = $("#first_node").val()
      n2 = $("#second_node").val();
      s1 = $("#first_script").val()
      s2 = $("#second_script").val();
  $.ajax({
    type: "POST",
    url: `/tasks/get_diff/${taskId}/${v1}/${v2}/${n1}/${n2}/${s1}/${s2}`,
    dataType: 'json',
    success: function(data){
      $("#view").append(diffview.buildView({
        baseTextLines: data.first,
        newTextLines: data.second,
        opcodes: data.opcodes,
        baseTextName: `${n1} - ${s1} - ${v1}`,
        newTextName: `${n2} - ${s2} - ${v2}`,
        contextSize: null,
        viewType: 0
      }));
    }
  });
});

function deleteTask(id) {
  $.ajax({
    type: "POST",
    url: `/tasks/delete_task/${id}`,
    success: function() {
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify('Task successfully deleted !', 'success', 5);
    }
  });
}

function pauseTask(id) {
  $.ajax({
    type: "POST",
    url: `/tasks/pause_task/${id}`,
    success: function() {
      $(`#pause-resume-${id}`).attr("onclick", `resumeTask('${id}')`).text('Resume');
      alertify.notify('Task paused !', 'success', 5);
    }
  });
}

function resumeTask(id) {
  $.ajax({
    type: "POST",
    url: `/tasks/resume_task/${id}`,
    success: function() {
      $(`#pause-resume-${id}`).attr("onclick", `pauseTask('${id}')`).text('Pause');
      alertify.notify('Task resumed !', 'success', 5);
    }
  });
}