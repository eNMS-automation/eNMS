/*
global
alertify: false
call: false
doc: false
initTable: false
*/

const toExclude = ['Action', 'Edit', 'Duplicate', 'Delete'];
let table = initTable('task', 'task', toExclude);
const taskManagement = true; // eslint-disable-line no-unused-vars

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

(function() {
  doc('https://enms.readthedocs.io/en/latest/scheduling/task_management.html');
  refreshTable(5000);
})();
