/*
global
addInstance: false
convertSelect: false
doc: false
instances: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Edit a service.
 * @param {values} values - Instance properties.
 * @param {instance} instance - Instance.
 */
function tableActions(values, instance) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('instance', '${instance.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('instance', '${instance.id}', true)">
    Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="confirmDeletion('instance', '${instance.id}')">Delete</button>`
  );
}

/**
 * Get Service Status.
 * @param {type} type - Service or Workflow.
 */
function getStatus(type) { // eslint-disable-line no-unused-vars
  call('/admin/get_cluster_status', function(status) {
    for (let i = 0; i < status.length; i++) {
      const col = table.column('#status');
      table.cell(i, col).data(status[i]).draw(false);
    }
    setTimeout(partial(getStatus, type), 5000);
  });
}

function scanCluster() { // eslint-disable-line no-unused-vars
  call('/admin/scan_cluster', function(cluster) {
    console.log(cluster);
  });
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  convertSelect('#instance-permissions');
  for (let i = 0; i < instances.length; i++) {
    addInstance('create', 'instance', instances[i]);
  }
})();
