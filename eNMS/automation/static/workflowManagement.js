/*
global
addInstance
call: false
doc: false
workflows: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Table Actions.
 * @param {values} values - values array.
 * @param {workflow} workflow - workflow.
 */
function tableActions(values, workflow) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showLogs('${workflow.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="compareLogs('${workflow.id}')"></i>Compare</a></button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runJob('${workflow.id}')">Run</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('workflow', '${workflow.id}')">Edit</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('workflow', '${workflow.id}')">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteInstance('workflow', '${workflow.id}')">Delete</button>`
  );
}

/**
 * Get Workflow States.
 */
function getStates() {
  call('/automation/get_states/workflow', function(states) {
    for (let i = 0; i < states.length; i++) {
      const col = table.column('#state');
      table.cell(i, col).data(states[i]).draw(false);
    }
    setTimeout(getStates, 1000);
  });
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/workflows/index.html');
  for (let i = 0; i < workflows.length; i++) {
    addInstance('create', 'workflow', workflows[i]);
  }
  convertSelect('workflow-devices', 'workflow-pools');
  getStates();
})();
