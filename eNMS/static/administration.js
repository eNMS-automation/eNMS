/*
global
alertify: false
doc: false
fCall: false
parameters: false
*/

/**
 * Save Parameters.
 */
// eslint-disable-next-line
function saveParameters() {
  fCall("/save_parameters", "#parameters-form", function() {
    alertify.notify("Parameters saved.", "success", 5);
  });
}

/**
* Get Cluster Status.
*/
function getClusterStatus() {
  call("/admin/get_cluster_status", function(cluster) {
    table.ajax.reload(null, false);
    setTimeout(getClusterStatus, 15000);
  });
}
getClusterStatus();

(function() {
  doc("https://enms.readthedocs.io/en/latest/security/access.html");
  $("#cluster_scan_protocol").val(parameters.cluster_scan_protocol);
  $("#default_view").val(parameters.default_view);
  $("#default_marker").val(parameters.default_marker);
  if (parameters.pool) {
    $("#pool").val(parameters.pool.id);
  }
})();
