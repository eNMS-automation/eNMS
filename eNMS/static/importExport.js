/*
global
alertify: false
doc: false
fCall: false
*/

document.getElementById("file").onchange = function() {
  importTopology("Device");
};

/**
 * Query openNMS server.
 */
// eslint-disable-next-line
function queryOpenNMS() {
  fCall("/inventory/query_opennms", "#opennms_form", function() {
    alertify.notify("Topology imported from OpenNMS.", "success", 5);
  });
}

/**
 * Query Netbox server.
 */
// eslint-disable-next-line
function queryNetbox() {
  fCall("/inventory/query_netbox", "#netbox_form", function() {
    alertify.notify("Topology imported from Netbox.", "success", 5);
  });
}

/**
 * Query libreNMS server.
 */
// eslint-disable-next-line
function queryLibreNMS() {
  fCall("/inventory/query_librenms", "#librenms_form", function() {
    alertify.notify("Topology imported from LibreNMS.", "success", 5);
  });
}

/**
 * Export project to Google Earth (creation of a .kmz file).
 */
// eslint-disable-next-line
function exportToGoogleEarth() {
  fCall("/inventory/export_to_google_earth", "#google-earth-form", function() {
    alertify.notify("Project exported to Google Earth.", "success", 5);
  });
}

/**
 * Export topology.
 */
// eslint-disable-next-line
function exportTopology() {
  alertify.notify("Topology export starting...", "success", 5);
  fCall("/inventory/export_topology", "#import-form", function() {
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
      url: "/inventory/import_topology",
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

(function() {
  doc("https://enms.readthedocs.io/en/latest/inventory/objects.html");
})();
