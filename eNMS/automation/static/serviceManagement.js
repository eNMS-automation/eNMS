/*
global
addInstance: false
doc: false
getStatus: false
services: false
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
 * Table Actions.
 * @param {values} values - values array.
 * @param {service} service - service.
 */
function tableActions(values, service) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showLogs('${service.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runJob('${service.id}')">Run</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="editService('${service.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="editService('${service.id}', true)">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="confirmDeletion('service', '${service.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/services/index.html');
  for (let i = 0; i < services.length; i++) {
    addInstance('create', 'service', services[i]);
  }
  getStatus('service');
})();
