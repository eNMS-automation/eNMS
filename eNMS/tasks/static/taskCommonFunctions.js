function showTaskModal(id) {
  taskId = id;
  $.ajax({
    type: "POST",
    url: `/tasks/get/${id}`,
    dataType: 'json',
    success: function(properties) {
      for (const [property, value] of Object.entries(properties)) {
        if(typeof(value) === "boolean") {
          $(`#${property}`).prop('checked', value);
        } else {
          $(`#${property}`).val(value);
        }
      }
      $('#job').val(properties.job.id);
      $('#nodes').val(properties.nodes.map(n => n.id));
      $('#pools').val(properties.pools.map(p => p.id));
    }
  });
  $('#scheduling').modal('show');
}

function runTask(id) {
  $.ajax({
    type: "POST",
    url: `/tasks/run_task/${id}`,
    dataType: 'json',
    success: function(task) {
      console.log(task);
      alertify.notify(`Task '${task.name}' started`, 'success', 5);
    }
  });
}

function scheduleScript() {
  if ($("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/tasks/scheduler",
      dataType: "json",
      data: $("#scheduling-form").serialize(),
      success: function(task) {
        alertify.notify(`Task '${task.name}' edited`, 'success', 5);
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
      $("#first_version,#second_version,#first_node,#second_node").empty();
      for (var i = 0; i < results.versions.length; i++) {
        value = results.versions[i];
        $("#first_version,#second_version").append($("<option></option>")
          .attr("value", value).text(value));
      }
      for (var i = 0; i < results.nodes.length; i++) {
        value = results.nodes[i];
        $("#first_node,#second_node").append($("<option></option>")
          .attr("value", value).text(value));
      }
    }
  });
  $('#compare-logs-modal').modal('show');
}

$("#first_version,#second_version,#first_node,#second_node").on('change', function() {
  $("#view").empty();
  var v1 = $("#first_version").val()
  var v2 = $("#second_version").val()
  var n1 = $("#first_node").val()
  var n2 = $("#second_node").val();
  $.ajax({
    type: "POST",
    url: `/tasks/get_diff/${taskId}/${v1}/${v2}/${n1}/${n2}`,
    dataType: 'json',
    success: function(data){
      $("#view").append(diffview.buildView({
        baseTextLines: data.first,
        newTextLines: data.second,
        opcodes: data.opcodes,
        baseTextName: `${n1} - ${v1}`,
        newTextName: `${n2} - ${v2}`,
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
      alertify.notify('Task successfully deleted.', 'success', 5);
    }
  });
}

function pauseTask(id) {
  $.ajax({
    type: "POST",
    url: `/tasks/pause_task/${id}`,
    success: function() {
      $(`#pause-resume-${id}`).attr(
        "onclick",
        `resumeTask('${id}')`
    ).text('Resume');
      alertify.notify('Task paused.', 'success', 5);
    }
  });
}

function resumeTask(id) {
  $.ajax({
    type: "POST",
    url: `/tasks/resume_task/${id}`,
    success: function() {
      $(`#pause-resume-${id}`).attr(
        "onclick",
        `pauseTask('${id}')`
    ).text('Pause');
      alertify.notify('Task resumed.', 'success', 5);
    }
  });
}