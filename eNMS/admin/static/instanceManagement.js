/*
global
alertify: false
call: false
convertSelect: false
doc: false
initTable: false
*/

let table = initTable("instance", "instance", ["Edit", "Duplicate", "Delete"]);

/**
 * Get Cluster Status.
 */
function getClusterStatus() {
  call("/admin/get_cluster_status", function(cluster) {
    table.ajax.reload(null, false);
    setTimeout(getClusterStatus, 15000);
  });
}

(function() {
  doc("https://enms.readthedocs.io/en/latest/security/access.html");
  getClusterStatus();
})();
