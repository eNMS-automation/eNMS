/*
global
alertify: false
call: false
doc: false
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
  const status = properties.status == 'Active' ? 'pause' : 'resume';
  values.push(
    `<button id="pause-resume-${properties.id}" type="button"
    class="btn btn-success btn-xs" onclick="${status}Task('${properties.id}')">
    ${status.charAt(0).toUpperCase() + status.substr(1)}</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTaskModal('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTaskModal('${properties.id}', true)">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="confirmDeletion('task', '${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

/**
 * Start or shutdown the scheduler.
 * @param {action} action - Pause or resume.
 */
function scheduler(action) { // eslint-disable-line no-unused-vars
  call(`/scheduling/scheduler/${action}`, function() {
      alertify.notify(`Scheduler ${action}d.`, 'success', 5);
    }
  );
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

/**
 * Get Task Status.
 */
function getStatus() {
  call(`/scheduling/get_status`, function(status) {
    for (let i = 0; i < status.length; i++) {
      const col = table.column('#status');
      table.cell(i, col).data(status[i]).draw(false);
    }
    setTimeout(getStatus, 5000);
  });
}

(function() {
  for (let i = 0; i < tasks.length; i++) {
    addTask('create', tasks[i]);
  }
  doc('https://enms.readthedocs.io/en/latest/scheduling/task_management.html');
  getStatus();
})();
