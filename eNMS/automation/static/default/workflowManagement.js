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
 * @param {properties} properties - Properties of the workflow.
 */
function addWorkflow(mode, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showLogs('${properties.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="compareLogs('${properties.id}')"></i>Compare</a></button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showWorkflowModal('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runJob('${properties.id}')">Run</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteWorkflow('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
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
 * Open the workflow modal for editing.
 * @param {id} id - Id of the workflow to edit.
 */
function showWorkflowModal(id) { // eslint-disable-line no-unused-vars
  call(`/automation/get/${id}`, function(properties) {
    $('#title').text(`Edit Workflow`);
    for (const [property, value] of Object.entries(properties)) {
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
    properties.devices.map(
      (n) => $(`.fs-option[data-value='${n.id}']`).click()
    );
    $('#pools').val(properties.pools.map((p) => p.id));
    $(`#edit`).modal('show');
  });
}

/**
 * Edit a workflow.
 */
function editObject() { // eslint-disable-line no-unused-vars
  fCall('/automation/edit_workflow', '#edit-form', function(properties) {
    const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
    addWorkflow(mode, properties);
    const message = `Workflow ${properties.name};
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
