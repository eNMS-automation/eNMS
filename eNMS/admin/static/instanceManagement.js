/*
global
addInstance: false
alertify: false
call: false
convertSelect: false
doc: false
instances: false
*/

perColumnSearch('instance', 'instance', [
  'Edit',
  'Duplicate',
  'Delete',
]);

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
  getClusterStatus();
})();
