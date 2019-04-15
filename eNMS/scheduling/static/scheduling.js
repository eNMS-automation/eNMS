/*
global
alertify: false
call: false
doc: false
initTable: false
refreshTable: false
*/

// eslint-disable-next-line no-unused-vars
let table = initTable("task", "task", [
  "Next runtime",
  "Time before next run",
  "Action",
  "Edit",
  "Duplicate",
  "Delete",
]);
const taskManagement = true; // eslint-disable-line no-unused-vars

/**
 * Pause a task.
 * @param {id} id - Task id.
 */
// eslint-disable-next-line
function pauseTask(id) {
  // eslint-disable-line no-unused-vars
  call(`/scheduling/pause_task/${id}`, function(result) {
    $(`#pause-resume-${id}`)
      .attr("onclick", `resumeTask('${id}')`)
      .text("Resume");
    alertify.notify("Task paused.", "success", 5);
  });
}

/**
 * Resume a task.
 * @param {id} id - Task id.
 */
// eslint-disable-next-line
function resumeTask(id) {
  // eslint-disable-line no-unused-vars
  call(`/scheduling/resume_task/${id}`, function(result) {
    $(`#pause-resume-${id}`)
      .attr("onclick", `pauseTask('${id}')`)
      .text("Pause");
    alertify.notify("Task resumed.", "success", 5);
  });
}

(function() {
  doc("https://enms.readthedocs.io/en/latest/scheduling/task_management.html");
  refreshTable(10000);
})();
