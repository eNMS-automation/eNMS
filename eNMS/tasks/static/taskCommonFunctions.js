/*
global
alertify: false
diffview: false
table: false
*/

let taskId;

/**
 * Show the scheduling modal for task.
 * @param {id} id - Task id.
 */
function showTaskModal(id) { // eslint-disable-line no-unused-vars
  taskId = id;
  $.ajax({
    type: 'POST',
    url: `/tasks/get/${id}`,
    dataType: 'json',
    success: function(properties) {
      for (const [property, value] of Object.entries(properties)) {
        if (typeof(value) === 'boolean') {
          $(`#${property}`).prop('checked', value);
        } else {
          $(`#${property}`).val(value);
        }
      }
      $('#job').val(properties.job.id);
      $('#devices').val(properties.devices.map((n) => n.id));
      $('#pools').val(properties.pools.map((p) => p.id));
    },
  });
  $('#scheduling').modal('show');
}

/**
 * Run task.
 * @param {id} id - Task id.
 */
function runTask(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/tasks/run_task/${id}`,
    dataType: 'json',
    success: function(task) {
      alertify.notify(`Task '${task.name}' started`, 'success', 5);
    },
  });
}

/**
 * Show the logs modal for a task.
 * @param {id} id - Task id.
 */
function showTaskLogs(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/tasks/show_logs/${id}`,
    dataType: 'json',
    success: function(logs) {
      $('#logs').text(logs);
    },
  });
  $(`#show-logs-modal`).modal('show');
}

/**
 * Show the compare logs modal for task.
 * @param {id} id - Task id.
 */
function compareTaskLogs(id) { // eslint-disable-line no-unused-vars
  taskId = id;
  $.ajax({
    type: 'POST',
    url: `/tasks/compare_logs/${id}`,
    dataType: 'json',
    success: function(results) {
      $('#first_version,#second_version,#first_device,#second_device').empty();
      for (let i = 0; i < results.versions.length; i++) {
        const value = results.versions[i];
        $('#first_version,#second_version').append($('<option></option>')
          .attr('value', value).text(value));
      }
      for (let i = 0; i < results.devices.length; i++) {
        const value = results.devices[i];
        $('#first_device,#second_device').append($('<option></option>')
          .attr('value', value).text(value));
      }
    },
  });
  $('#compare-logs-modal').modal('show');
}

const dropDowns = '#first_version,#second_version,#first_device,#second_device';
$(dropDowns).on('change', function() {
  $('#view').empty();
  const v1 = $('#first_version').val();
  const v2 = $('#second_version').val();
  const n1 = $('#first_device').val();
  const n2 = $('#second_device').val();
  $.ajax({
    type: 'POST',
    url: `/tasks/get_diff/${taskId}/${v1}/${v2}/${n1}/${n2}`,
    dataType: 'json',
    success: function(data) {
      $('#view').append(diffview.buildView({
        baseTextLines: data.first,
        newTextLines: data.second,
        opcodes: data.opcodes,
        baseTextName: `${n1} - ${v1}`,
        newTextName: `${n2} - ${v2}`,
        contextSize: null,
        viewType: 0,
      }));
    },
  });
});

/**
 * Delete a task.
 * @param {id} id - Task id.
 */
function deleteTask(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/tasks/delete_task/${id}`,
    success: function() {
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify('Task successfully deleted.', 'success', 5);
    },
  });
}

/**
 * Pause a task.
 * @param {id} id - Task id.
 */
function pauseTask(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/tasks/pause_task/${id}`,
    success: function() {
      $(`#pause-resume-${id}`).attr(
        'onclick',
        `resumeTask('${id}')`
    ).text('Resume');
      alertify.notify('Task paused.', 'success', 5);
    },
  });
}

/**
 * Resume a task.
 * @param {id} id - Task id.
 */
function resumeTask(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/tasks/resume_task/${id}`,
    success: function() {
      $(`#pause-resume-${id}`).attr(
        'onclick',
        `pauseTask('${id}')`
    ).text('Pause');
      alertify.notify('Task resumed.', 'success', 5);
    },
  });
}
