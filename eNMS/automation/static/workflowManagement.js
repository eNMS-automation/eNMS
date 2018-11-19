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

let pageScrollPos;
const table = $('#table').DataTable({ // eslint-disable-line
  'preDrawCallback': function(settings) {
    pageScrollPos = $(window).scrollTop();
  },
  'drawCallback': function(settings) {
    $(window).scrollTop(pageScrollPos);
  },
});

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

/**
 * Table Actions.
 * @param {values} values - values array.
 * @param {workflow} workflow - workflow.
 */
function tableActions(values, workflow) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showLogs('${workflow.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runJob('${workflow.id}')">Run</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('workflow', '${workflow.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showWorkflowModalDuplicate('${workflow.id}')">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="confirmDeletion('workflow', '${workflow.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/workflows/index.html');
  for (let i = 0; i < workflows.length; i++) {
    addInstance('create', 'workflow', workflows[i]);
  }
  convertSelect('#workflow-devices', '#workflow-pools');
  $('#edit-workflow').on('hidden.bs.modal', function() {
    $('#workflow-button').attr('onclick', 'processData("workflow")');
  });
  getStatus('workflow');
})();
