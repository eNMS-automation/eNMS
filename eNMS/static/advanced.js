/*
global
alertify: false
call: false
convertSelect: false
doc: false
fCall: false
folders: false
*/

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
  folders.forEach((f) => {
    $("#versions").append(`<option value='${f}'></option>`);
  });
  doc("https://enms.readthedocs.io/en/latest/base/migrations.html");
})();
