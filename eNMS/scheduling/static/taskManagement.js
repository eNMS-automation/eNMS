/*
global
alertify: false
call: false
doc: false
fCall: false
fields: false
tasks: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap
const taskManagement = true; // eslint-disable-line no-unused-vars

/**
 * Add a task to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {properties} properties - Properties of the task to add.
 */
function addTask(mode, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    if (fields[i] != 'recurrent') {
      values.push(`${properties[fields[i]]}`);
    }
  }
  const status = properties.status == 'active' ? 'pause' : 'resume';
  values.push(
    `<button id="pause-resume-${properties.id}" type="button"
    class="btn btn-success btn-xs" onclick="${status}Task('${properties.id}')">
    ${status.charAt(0).toUpperCase() + status.substr(1)}</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTaskModal('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTaskModal('${properties.id}', true)">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteInstance('task', '${properties.id}')">Delete</button>`
  );

  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

/**
 * Schedule a task.
 */
function scheduleTask() { // eslint-disable-line no-unused-vars
  fCall('/update/task', '#task-modal-form', function(task) {
    const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
    addTask(mode, task);
    const message = `Task '${task.name}'
    ${mode == 'edit' ? 'edited' : 'created'} !`;
    alertify.notify(message, 'success', 5);
    $('#task-modal').modal('hide');
  });
}

/**
 * Pause a task.
 * @param {id} id - Task id.
 */
function pauseTask(id) { // eslint-disable-line no-unused-vars
  call(`/scheduling/pause_task/${id}`, function(result) {
    $(`#pause-resume-${id}`).attr(
      'onclick',
      `resumeTask('${id}')`
    ).text('Resume');
    alertify.notify('Task paused.', 'success', 5);
  });
}

/**
 * Resume a task.
 * @param {id} id - Task id.
 */
function resumeTask(id) { // eslint-disable-line no-unused-vars
  call(`/scheduling/resume_task/${id}`, function(result) {
    $(`#pause-resume-${id}`).attr(
      'onclick',
      `pauseTask('${id}')`
    ).text('Pause');
    alertify.notify('Task resumed.', 'success', 5);
  });
}

(function() {
  if (typeof tasks !== 'undefined') {
    for (let i = 0; i < tasks.length; i++) {
      addTask('create', tasks[i]);
    }
  }
  const dates = ['start_date', 'end_date'];
  const today = new Date();
  for (let i = 0; i < dates.length; i++) {
    $('#' + dates[i]).datetimepicker({
      format: 'DD/MM/YYYY HH:mm:ss',
      widgetPositioning: {
        horizontal: 'left',
        vertical: 'bottom',
      },
      useCurrent: false,
    });
    if ($('#' + dates[i]).length) {
      $('#' + dates[i]).data('DateTimePicker').minDate(today);
    }
  }
  doc('https://enms.readthedocs.io/en/latest/scheduling/task_management.html');
})();
