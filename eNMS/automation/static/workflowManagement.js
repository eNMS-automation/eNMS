/*
global
alertify: false
call: false
doc: false
fCall: false
fields: false
propertyTypes: false
workflows: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

(function() {
  $('#devices').fSelect({
    placeholder: 'Select devices',
    numDisplayed: 5,
    overflowText: '{n} devices selected',
    noResultsText: 'No results found',
  });
})();

/**
 * Table Actions.
 * @param {values} values - values array.
 * @param {pool} pool - Pool.
 */
function tableActions(values, pool) { // eslint-disable-line no-unused-vars
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
 * Add workflow to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {workflow} workflow - Workflow.
 */
function addWorkflow(mode, workflow) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${workflow[fields[i]]}`);
  }

  if (mode == 'edit') {
    table.row($(`#${workflow.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${workflow.id}`);
  }
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
    addWorkflow('create', workflows[i]);
  }
  getStates();
})();
