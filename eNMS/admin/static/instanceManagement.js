/*
global
addInstance: false
alertify: false
call: false
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
 * Get Cluster Status.
 */
function getClusterStatus() { // eslint-disable-line no-unused-vars
  call('/admin/get_cluster_status', function(cluster) {
    for (const [property, value] of Object.entries(cluster)) {
      for (let i = 0; i < value.length; i++) {
        const col = table.column(`#${property}`);
        table.cell(i, col).data(value[i]).draw(false);
      }
    }
    setTimeout(getClusterStatus, 15000);
  });
}

/**
 * Scan Cluster subnet for new Instances.
 */
function scanCluster() { // eslint-disable-line no-unused-vars
  call('/admin/scan_cluster', function(cluster) {
    alertify.notify('Scan completed.', 'success', 5);
  });
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  convertSelect('#instance-permissions');
  for (let i = 0; i < instances.length; i++) {
    addInstance('create', 'instance', instances[i]);
  }
  getClusterStatus();
})();
