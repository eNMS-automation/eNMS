/*
global
call: false
doc: false
fields: false
services: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Add a service to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {service} service - Service properties.
 */
function addService(mode, service) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${service[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showLogs('${service.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="compareLogs('${service.id}')"></i>Compare</a></button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runJob('${service.id}')">Run</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="editService('${service.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="editService('${service.id}', true)">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteInstance('service', '${service.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${service.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${service.id}`);
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
  doc('https://enms.readthedocs.io/en/latest/services/index.html');
  for (let i = 0; i < services.length; i++) {
    addService('create', services[i]);
  }
  getStates();
})();

