/*
global
alertify: false
doc: false
fCall: false
folders: false
parameters: false
*/

/**
 * Show Parameters
 */
// eslint-disable-next-line
function showParameters(type) {
  createPanel(type, `${type} Parameters`, parametersPanelSize[type], 0, () => {
    call("/get-parameters-1", function(parameters) {
      for (const [property, value] of Object.entries(parameters)) {
        console.log(property, value);
        if ($(`#${property}`).length) {
          $(`#${property}`).val(value);
        }
      }
    });
  });
}

/**
 * Show Database Panel
 */
// eslint-disable-next-line
function showDatabasePanel(type) {
  createPanel(type, type, panelSize[type]);
}

/**
 * Show Admin Panel
 */
// eslint-disable-next-line
function showAdminPanel(type) {
  createPanel(type, type, panelSize[type], 0, () => {
    if (type == "excel") {
      document.getElementById("file").onchange = function() {
        importTopology("Device");
      };
    }
  });
}

/**
 * Query openNMS server.
 */
// eslint-disable-next-line
function queryOpenNMS() {
  fCall("/query_opennms", "#opennms-form", function() {
    alertify.notify("Topology imported from OpenNMS.", "success", 5);
  });
}

/**
 * Query Netbox server.
 */
// eslint-disable-next-line
function queryNetbox() {
  fCall("/query_netbox", "#netbox-form", function() {
    alertify.notify("Topology imported from Netbox.", "success", 5);
  });
}

/**
 * Query libreNMS server.
 */
// eslint-disable-next-line
function queryLibreNMS() {
  fCall("/query_librenms", "#librenms-form", function() {
    alertify.notify("Topology imported from LibreNMS.", "success", 5);
  });
}

/**
 * Export project to Google Earth (creation of a .kmz file).
 */
// eslint-disable-next-line
function exportToGoogleEarth() {
  fCall("/export_to_google_earth", "#google_earth_export-form", function() {
    alertify.notify("Project exported to Google Earth.", "success", 5);
  });
}

/**
 * Export topology.
 */
// eslint-disable-next-line
function exportTopology() {
  alertify.notify("Topology export starting...", "success", 5);
  fCall("/export_topology", "#excel_export-form", function() {
    alertify.notify("Topology successfully exported.", "success", 5);
  });
}

/**
 * Import topology.
 */
// eslint-disable-next-line
function importTopology() {
  alertify.notify("Topology import: starting...", "success", 5);
  if (
    $("#import-form")
      .parsley()
      .validate()
  ) {
    const formData = new FormData($("#import-form")[0]);
    $.ajax({
      type: "POST",
      url: "/import_topology",
      dataType: "json",
      data: formData,
      contentType: false,
      processData: false,
      async: true,
      success: function(result) {
        alertify.notify(result, "success", 5);
      },
    });
    $("#file")[0].value = "";
  }
}

/**
 * Save Parameters.
 */
// eslint-disable-next-line
function saveParameters(type) {
  fCall(`/save_parameters-${type}`, `#${type}-form`, function() {
    alertify.notify("Parameters saved.", "success", 5);
  });
  $(`#${type}`).remove();
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
  fCall("/migration_export", "#migration-form", function() {
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
function databaseDeletion() {
  alertify.notify("Starting to delete...", "success", 5);
  fCall("/database_helpers", "#deletion-form", function(result) {
    alertify.notify("Deletion done.", "success", 5);
    $("#deletion-form").remove();
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
  call(`/scheduler-${action}`, function() {
    alertify.notify(`Scheduler ${action}d.`, "success", 5);
  });
}

/**
 * Scan Cluster subnet for new Servers.
 */
// eslint-disable-next-line
function scanCluster() {
  alertify.notify("Scan started.", "success", 5);
  call("/scan_cluster", function(cluster) {
    alertify.notify("Scan completed.", "success", 5);
  });
}

(function() {
  if (page == "advanced") {
    folders.forEach((f) => {
      $("#versions").append(`<option value='${f}'></option>`);
    });
  } else if (page == "server_management") {
    getClusterStatus();
  }
})();
