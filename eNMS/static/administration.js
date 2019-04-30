/*
global
alertify: false
doc: false
fCall: false
folders: false
parameters: false
*/

/**
 * Save Parameters.
 */
// eslint-disable-next-line
function saveParameters(type) {
  fCall("/save_parameters", `#${type}-form`, function() {
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

/**
 * Export all for migration.
 */
// eslint-disable-next-line
function migrationsExport() {
  alertify.notify("Export initiated.", "success", 5);
  fCall("/migration_export", "#import-export-form", function() {
    alertify.notify("Export successful.", "success", 5);
  });
}

/**
 * Import all for migration.
 */
// eslint-disable-next-line
function migrationsImport() {
  alertify.notify("Import initiated.", "success", 5);
  fCall("/migration_import", "#import-export-form", function(result) {
    alertify.notify(result, "success", 5);
  });
}

/**
 * Database Helpers.
 */
// eslint-disable-next-line
function databaseHelpers() {
  alertify.notify("Starting to delete...", "success", 5);
  fCall("/database_helpers", "#database-helpers-form", function(result) {
    alertify.notify("Deletion done.", "success", 5);
  });
}

/**
 * Reset Status.
 */
// eslint-disable-next-line
function resetStatus() {
  call("/reset_status", function(result) {
    alertify.notify("Reset successful.", "success", 5);
  });
}

/**
 * Git Action.
 */
// eslint-disable-next-line
function getGitContent() {
  call("/get_git_content", function(result) {
    alertify.notify("Action successful.", "success", 5);
  });
}

/**
 * Start or shutdown the scheduler.
 * @param {action} action - Pause or resume.
 */
// eslint-disable-next-line
function scheduler(action) {
  call(`/scheduler/${action}`, function() {
    alertify.notify(`Scheduler ${action}d.`, "success", 5);
  });
}

/**
 * Scan Cluster subnet for new Instances.
 */
// eslint-disable-next-line
function scanCluster() {
  alertify.notify("Scan started.", "success", 5);
  call("/scan_cluster", function(cluster) {
    alertify.notify("Scan completed.", "success", 5);
  });
}


(function() {
  if (page == "administration") {
    /*
    $("#cluster_scan_protocol").val(parameters.cluster_scan_protocol);
    $("#default_view").val(parameters.default_view);
    $("#default_marker").val(parameters.default_marker);
    if (parameters.pool) {
      $("#pool").val(parameters.pool.id);
    }
    */
  } else if (page == "advanced") {
    folders.forEach((f) => {
      $("#versions").append(`<option value='${f}'></option>`);
    });
  } else if (page == "instance_management") {
    getClusterStatus();
  }
})();
