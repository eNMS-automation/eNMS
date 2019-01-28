/*
global
alertify: false
convertSelect: false
doc: false
fCall: false
getStatus: false
initTable: false
showTypeModal: false
*/

const toExclude = ['Logs', 'Run', 'Edit', 'Duplicate', 'Delete'];
let table = initTable('workflow', 'workflow', toExclude);

/**
 * Display instance modal for editing.
 * @param {id} id - Instance ID.
 */
function showWorkflowModalDuplicate(id) { // eslint-disable-line no-unused-vars
  $('#workflow-button').attr('onclick', `duplicateWorkflow(${id})`);
  showTypeModal('workflow', id, true);
}

/**
 * Display instance modal for editing.
 * @param {id} id - Instance ID.
 */
function duplicateWorkflow(id) { // eslint-disable-line no-unused-vars
  $('#edit-workflow').modal('hide');
  fCall(
    `/automation/duplicate_workflow/${id}`,
    '#edit-workflow-form',
    (workflow) => {
      table.ajax.reload(null, false);
      alertify.notify('Workflow successfully duplicated', 'success', 5);
    }
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/workflows/index.html');
  convertSelect('#workflow-devices', '#workflow-pools');
  $('#edit-workflow').on('hidden.bs.modal', function() {
    $('#workflow-button').attr('onclick', 'processData("workflow")');
  });
  refreshTable(5000);
})();
