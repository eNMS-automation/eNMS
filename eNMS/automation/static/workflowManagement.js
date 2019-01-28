/*
global
alertify: false
addInstance: false
convertSelect: false
doc: false
fCall: false
getStatus: false
showTypeModal: false
workflows: false
*/

/*
let pageScrollPos;
const table = $('#table').DataTable({ // eslint-disable-line
  'preDrawCallback': function(settings) {
    pageScrollPos = $(window).scrollTop();
  },
  'drawCallback': function(settings) {
    $(window).scrollTop(pageScrollPos);
  },
});
*/

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
      addInstance('create', 'workflow', workflow);
      alertify.notify('Workflow successfully duplicated', 'success', 5);
    }
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/workflows/index.html');
  table = perColumnSearch('workflow', 'workflow', [
    'Logs',
    'Run',
    'Edit',
    'Duplicate',
    'Delete'
  ]);
  convertSelect('#workflow-devices', '#workflow-pools');
  $('#edit-workflow').on('hidden.bs.modal', function() {
    $('#workflow-button').attr('onclick', 'processData("workflow")');
  });
  getStatus('workflow');
})();
