/*
global
alertify: false
call: false
convertSelect: false
doc: false
initTable: false
*/

let table = initTable('instance', 'instance', ['Edit', 'Duplicate', 'Delete']);

/**
 * Get Cluster Status.
 */
function getClusterStatus() { // eslint-disable-line no-unused-vars
  call('/admin/get_cluster_status', function(cluster) {
    table.ajax.reload(null, false);
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
