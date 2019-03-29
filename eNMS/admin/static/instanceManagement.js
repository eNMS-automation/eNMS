/*
global
alertify: false
*/

import { call, convertSelect, doc, initTable } from "../../static/enms/base.js";

window.table = initTable("instance", "instance", [
  "Edit",
  "Duplicate",
  "Delete",
]);

/**
 * Get Cluster Status.
 */
function getClusterStatus() {
  call("/admin/get_cluster_status", function(cluster) {
    console.log(cluster);
    window.table.ajax.reload(null, false);
    setTimeout(getClusterStatus, 15000);
  });
}

/**
 * Scan Cluster subnet for new Instances.
 */
window.scanCluster = function() {
  alertify.notify("Scan started.", "success", 5);
  call("/admin/scan_cluster", function(cluster) {
    alertify.notify("Scan completed.", "success", 5);
  });
};

(function() {
  doc("https://enms.readthedocs.io/en/latest/security/access.html");
  convertSelect("#instance-permissions");
  getClusterStatus();
})();
