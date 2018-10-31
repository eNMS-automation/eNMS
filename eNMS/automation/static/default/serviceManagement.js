/*
global
alertify: false
call: false
fields: false
services: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add a service to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {properties} properties - Properties of the service.
 */
function addService(mode, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showLogs('${properties.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="compareLogs('${properties.id}')"></i>Compare</a></button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runJob('${properties.id}')">Run</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="editService('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteService('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

/**
 * Get Service States.
 */
function getStates() {
  call('/automation/get_states/service', function(states) {
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
    'https://enms.readthedocs.io/en/latest/services/index.html'
  );
  for (let i = 0; i < services.length; i++) {
    addService('create', services[i]);
  }
  getStates();
})();

/**
 * Delete a service.
 * @param {id} id - Id of the service to delete.
 */
function deleteService(id) { // eslint-disable-line no-unused-vars
  call(`/automation/delete/${id}`, function(service) {
    table.row($(`#${id}`)).remove().draw(false);
    const message = `Service '${service.name}' successfully deleted.`;
    alertify.notify(message, 'error', 5);
  });
}
