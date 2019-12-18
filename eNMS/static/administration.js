/*
global
alertify: false
call: false
config: true
createPanel: false
fCall: false
folders: false
JSONEditor: false
page: false
showPanel: false
tables: false
*/

import { showPanel } from './base.js';

let editor;

// eslint-disable-next-line
function showConfiguration() {
  createPanel("configuration", "Configuration", null, function() {
    editor = new JSONEditor(document.getElementById("content"), {}, config);
  });
}

// eslint-disable-next-line
function saveConfiguration() {
  $.ajax({
    type: "POST",
    url: "/save_configuration",
    contentType: "application/json",
    data: JSON.stringify(editor.get()),
    success: function() {
      config = editor.get();
      $("#configuration").remove();
      alertify.notify("Configuration saved.", "success", 5);
    },
  });
}

// eslint-disable-next-line
function showImportTopologyPanel(type) {
  createPanel("excel_import", "Import Topology as an Excel file", 0, () => {
    document.getElementById("file").onchange = function() {
      importTopology();
    };
  });
}

// eslint-disable-next-line
function queryOpenNMS() {
  call("/query_opennms", function() {
    alertify.notify("Topology imported from OpenNMS.", "success", 5);
  });
}

// eslint-disable-next-line
function queryNetbox() {
  call("/query_netbox", function() {
    alertify.notify("Topology imported from Netbox.", "success", 5);
  });
}

// eslint-disable-next-line
function queryLibreNMS() {
  call("/query_librenms", function() {
    alertify.notify("Topology imported from LibreNMS.", "success", 5);
  });
}

// eslint-disable-next-line
function exportTopology() {
  alertify.notify("Topology export starting...", "success", 5);
  fCall("/export_topology", "excel_export-form", function() {
    alertify.notify("Topology successfully exported.", "success", 5);
  });
}

// eslint-disable-next-line
function importTopology() {
  alertify.notify("Topology import: starting...", "success", 5);
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

function getClusterStatus() {
  call("/get_cluster_status", function(cluster) {
    tables["server"].ajax.reload(null, false);
    setTimeout(getClusterStatus, 15000);
  });
}

// eslint-disable-next-line
function migrationsExport() {
  alertify.notify("Export initiated.", "success", 5);
  fCall("/migration_export", "migration-form", function() {
    alertify.notify("Export successful.", "success", 5);
  });
}

// eslint-disable-next-line
function showMigrationPanel() {
  showPanel("database_migration", null, () => {
    let list = document.getElementById("versions");
    folders.forEach((item) => {
      let option = document.createElement("option");
      option.textContent = option.value = item;
      list.appendChild(option);
    });
  });
}

// eslint-disable-next-line
function migrationsImport() {
  alertify.notify("Import initiated.", "success", 5);
  fCall("/migration_import", "migration-form", function(result) {
    alertify.notify(result, "success", 5);
  });
}

function refreshExportedServices() {
  call("/get_exported_services", function(services) {
    let list = document.getElementById("service");
    services.forEach((item) => {
      let option = document.createElement("option");
      option.textContent = option.value = item;
      list.appendChild(option);
    });
    $("#service").selectpicker("refresh");
  });
}

// eslint-disable-next-line
function showImportServicePanel() {
  showPanel("import_service", null, () => {
    refreshExportedServices();
  });
}

// eslint-disable-next-line
function importService() {
  call(`/import_service/${$("#service").val()}`, function(result) {
    alertify.notify("Import successful.", "success", 5);
    $("#import_service").remove();
  });
}

// eslint-disable-next-line
function databaseDeletion() {
  alertify.notify("Starting to delete...", "success", 5);
  fCall("/database_deletion", "database_deletion-form", function(result) {
    alertify.notify("Deletion done.", "success", 5);
    $("#deletion-form").remove();
  });
}

// eslint-disable-next-line
function getGitContent() {
  call("/get_git_content", function(result) {
    alertify.notify("Action successful.", "success", 5);
  });
}

// eslint-disable-next-line
function scheduler(action) {
  call(`/scheduler_action/${action}`, function() {
    alertify.notify(`Scheduler ${action}d.`, "success", 5);
  });
}

// eslint-disable-next-line
function scanCluster() {
  alertify.notify("Scan started.", "success", 5);
  call("/scan_cluster", function(cluster) {
    alertify.notify("Scan completed.", "success", 5);
  });
}

// eslint-disable-next-line
function deleteFile(file) {
  call(`/delete_file/${file.data.path.replace(/\//g, ">")}`, function() {
    $("#files-tree")
      .jstree()
      .delete_node(file.id);
    alertify.notify(
      `File ${file.data.name} successfully deleted.`,
      "success",
      5
    );
  });
}

// eslint-disable-next-line
function editFile(file) {
  const filepath = file.data.path.replace(/\//g, ">");
  call(`/edit_file/${filepath}`, function(content) {
    createPanel("file", `Edit ${file.data.path}`, filepath, () => {
      const display = document.getElementById(`file_content-${filepath}`);
      // eslint-disable-next-line new-cap
      let editor = CodeMirror.fromTextArea(display, {
        lineWrapping: true,
        lineNumbers: true,
        theme: "cobalt",
        matchBrackets: true,
        mode: "python",
        extraKeys: { "Ctrl-F": "findPersistent" },
        scrollbarStyle: "overlay",
      });
      editor.setSize("100%", "100%");
      editors[filepath] = editor;
      editor.setValue(content);
    });
  });
}

// eslint-disable-next-line
function saveFile(file) {
  $(`[id="file_content-${file}"]`).text(editors[file].getValue());
  fCall(`/save_file/${file}`, `file-content-form-${file}`, function() {
    alertify.notify("File successfully saved.", "success", 5);
    $(`[id="file-${file}"`).remove();
  });
}

// eslint-disable-next-line
function showFileUploadPanel(folder) {
  const path = folder.replace(/\//g, ">");
  createPanel("upload_files", `Upload files to ${folder}`, path, () => {
    const element = document.getElementById(`dropzone-${path}`);
    let dropzone = new Dropzone(element, {
      url: "/upload_files",
      autoProcessQueue: false,
    });
    $(`[id="dropzone-submit-${path}"]`).click(function() {
      $(`[id="folder-${path}"]`).val(folder);
      dropzone.processQueue();
      alertify.notify("File successfully uploaded.", "success", 5);
      $(`[id="upload_files-${path}"]`).remove();
    });
  });
}

// eslint-disable-next-line
function createNewFolder() {}

// eslint-disable-next-line
window.eNMS.displayFiles = function() {
  showPanel("files", null, function() {
    $("#files-tree").jstree({
      core: {
        animation: 200,
        themes: { stripes: true, variant: "large" },
        check_callback: true,
        data: {
          url: function(node) {
            const path = node.id == "#" ? "root" : node.data.path;
            return `/get_tree_files/${path.replace(/\//g, ">")}`;
          },
          type: "POST",
        },
      },
      plugins: ["html_row", "state", "types", "wholerow"],
      types: {
        file: {
          icon: "jstree-icon jstree-file",
        },
      },
      html_row: {
        default: function(el, node) {
          if (!node) return;
          if (node.type == "file") {
            const data = JSON.stringify(node);
            $(el).find("a").append(`
              <div style="position: absolute; top: 0px; right: 200px">
                ${node.data.modified}
              </div>
              <div style="position: absolute; top: 0px; right: 50px">
                <button type="button"
                  class="btn btn-xs btn-primary"
                  onclick='editFile(${data})'
                >
                  <span class="glyphicon glyphicon-edit"></span>
                </button>
                <button type="button"
                class="btn btn-xs btn-info"
                onclick="location.href='/download_file/${node.data.path}'"
                >
                <span class="glyphicon glyphicon-download"></span>
                </button>
                <button type="button"
                  class="btn btn-xs btn-danger"
                  onclick='deleteFile(${data})'
                >
                  <span class="glyphicon glyphicon-trash"></span>
                </button>
              </div>
              `);
          } else {
            $(el).find("a").append(`
              <div style="position: absolute; top: 0px; right: 50px">
              <button type="button"
              class="btn btn-xs btn-primary"
              onclick="showFileUploadPanel('${node.data.path}')"
            >
              <span class="glyphicon glyphicon-plus"></span>
            </button>
              </div>
              `);
          }
        },
      },
    });
  });
}
