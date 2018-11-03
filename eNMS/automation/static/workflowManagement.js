/*
global
alertify: false
call: false
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
 * Add workflow to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {workflow} workflow - Workflow.
 */
function addWorkflow(mode, workflow) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${workflow[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showLogs('${workflow.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="compareLogs('${workflow.id}')"></i>Compare</a></button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runJob('${workflow.id}')">Run</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showWorkflowModal('${workflow.id}')">Edit</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showDuplicateWorkflowModal('${workflow.id}')">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteWorkflow('${workflow.id}')">Delete</button>`
  );
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
  $('#doc-link').attr(
    'href',
    'https://enms.readthedocs.io/en/latest/workflows/index.html'
  );
  for (let i = 0; i < workflows.length; i++) {
    addWorkflow('create', workflows[i]);
  }
  getStates();
})();

/**
 * Open the workflow modal for creation.
 */
function showModal() { // eslint-disable-line no-unused-vars
  $('#title').text('Create a New Workflow');
  $('#edit-form').trigger('reset');
  $('#edit').modal('show');
}

/**
 * Open the name modal for workflow duplication.
 */
function showDuplicateWorkflowModal(id) { // eslint-disable-line no-unused-vars
  jobId = id;
  $('#name-modal').trigger('reset');
  $('#name-modal').modal('show');
}

/**
 * Open the workflow modal for editing.
 * @param {id} id - Id of the workflow to edit.
 */
function showWorkflowModal(id) { // eslint-disable-line no-unused-vars
  call(`/automation/get/${id}`, function(workflow) {
    $('#title').text(`Edit Workflow`);
    for (const [property, value] of Object.entries(workflow)) {
      const propertyType = propertyTypes[property] || 'str';
      if (propertyType.includes('bool')) {
        $(`#${property}`).prop('checked', value);
      } else if (propertyType.includes('dict')) {
        $(`#${property}`).val(value ? JSON.stringify(value): '{}');
      } else {
        $(`#${property}`).val(value);
      }
    }
    $('.fs-option').removeClass('selected');
    $('.fs-label').text('Select devices');
    workflow.devices.map(
      (n) => $(`.fs-option[data-value='${n.id}']`).click()
    );
    $('#pools').val(workflow.pools.map((p) => p.id));
    $(`#edit`).modal('show');
  });
}

/**
 * Edit a workflow.
 */
function editObject() { // eslint-disable-line no-unused-vars
  fCall('/automation/edit_workflow', '#edit-form', function(workflow) {
    const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
    addWorkflow(mode, workflow);
    const message = `Workflow ${workflow.name};
    ${mode == 'edit' ? 'edited' : 'created'}.`;
    alertify.notify(message, 'success', 5);
    $(`#edit`).modal('hide');
  });
}

/**
 * Delete a workflow.
 * @param {id} id - Id of the workflow to delete.
 */
function deleteWorkflow(id) { // eslint-disable-line no-unused-vars
  call(`/automation/delete_workflow/${id}`, function(workflow) {
    table.row($(`#${id}`)).remove().draw(false);
    alertify.notify(`Workflow '${workflow.name}' deleted.`, 'error', 5);
  });
}
