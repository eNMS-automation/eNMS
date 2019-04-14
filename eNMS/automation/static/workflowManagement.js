/*
global
alertify: false
convertSelect: false
doc: false
fCall: false
initTable: false
refreshTable: false
showTypePanel: false
*/

const toExclude = ["Logs", "Results", "Run", "Edit", "Duplicate", "Delete"];
// eslint-disable-next-line no-unused-vars
let table = initTable("workflow", "workflow", toExclude);

/**
 * Display instance modal for editing.
 * @param {id} id - Instance ID.
 */
// eslint-disable-next-line
function showWorkflowModalDuplicate(id) {
  $("#workflow-button").attr("onclick", `duplicateWorkflow(${id})`);
  showTypePanel("workflow", id, true);
}

/**
 * Display instance modal for editing.
 * @param {id} id - Instance ID.
 */
// eslint-disable-next-line
function duplicateWorkflow(id) {
  $("#edit-workflow").modal("hide");
  fCall(
    `/automation/duplicate_workflow/${id}`,
    "#edit-workflow-form",
    (workflow) => {
      table.ajax.reload(null, false);
      alertify.notify("Workflow successfully duplicated", "success", 5);
    }
  );
}

(function() {
  doc("https://enms.readthedocs.io/en/latest/workflows/index.html");
  refreshTable(5000);
})();
