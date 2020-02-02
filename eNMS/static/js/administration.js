/*
global
CodeMirror: false
settings: true
Dropzone: false
JSONEditor: false
*/

import {
  call,
  configureNamespace,
  editors,
  fCall,
  notify,
  openPanel,
} from "./base.js";
import { tables } from "./table.js";

let settingsEditor;

function showImportTopologyPanel() {
  openPanel({
    name: "excel_import", title: "Import Topology as an Excel file",
    processing: () => {
      document.getElementById("file").onchange = function() {
        importTopology();
      };
    }
  });
}

function saveSettings() {
  $.ajax({
    type: "POST",
    url: "/save_settings",
    contentType: "application/json",
    data: JSON.stringify(settingsEditor.get()),
    success: function() {
      settings = settingsEditor.get();
      $("#settings").remove();
      notify("Settings saved.", "success", 5);
    },
  });
}

function showSettings() {
  openPanel({
    name: "settings",
    title: "Settings",
    processing: function() {
      settingsEditor = new JSONEditor(
        document.getElementById("content"),
        {},
        settings
      );
    }
  });
}

function exportTopology() {
  notify("Topology export starting...", "success", 5);
  fCall("/export_topology", "excel_export-form", function() {
    notify("Topology successfully exported.", "success", 5);
  });
}

function importTopology() {
  notify("Topology import: starting...", "success", 5);
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
      notify(result, "success", 5);
    },
  });
  $("#file")[0].value = "";
}

function getClusterStatus() {
  call("/get_cluster_status", function() {
    tables["server"].ajax.reload(null, false);
    setTimeout(getClusterStatus, 15000);
  });
}

function migrationsExport() {
  notify("Export initiated.", "success", 5);
  fCall("/migration_export", "migration-form", function() {
    notify("Export successful.", "success", 5);
  });
}

function showMigrationPanel() {
  openPanel({
    name: "database_migration",
    processing: () => {
      call("/get_migration_folders", function(folders) {
        let list = document.getElementById("versions");
        folders.forEach((item) => {
          let option = document.createElement("option");
          option.textContent = option.value = item;
          list.appendChild(option);
        });
      });
    }
  });
}

function migrationsImport() {
  notify("Import initiated.", "success", 5);
  fCall("/migration_import", "migration-form", function(result) {
    notify(result, "success", 5);
  });
}

function showImportServicePanel() {
  openPanel({
    name: "import_service",
    processing: () => {
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
  });
}

function importService() {
  call(`/import_service/${$("#service").val()}`, function(result) {
    notify("Import successful.", "success", 5);
    $("#import_service").remove();
  });
}

function databaseDeletion() {
  notify("Starting to delete...", "success", 5);
  fCall("/database_deletion", "database_deletion-form", function(result) {
    notify("Deletion done.", "success", 5);
    $("#deletion-form").remove();
  });
}

function getGitContent() {
  call("/get_git_content", function(result) {
    notify("Action successful.", "success", 5);
  });
}

function scanCluster() {
  notify("Scan started.", "success", 5);
  call("/scan_cluster", function(cluster) {
    notify("Scan completed.", "success", 5);
  });
}

function deleteFile(file) {
  call(`/delete_file/${file.data.path.replace(/\//g, ">")}`, function() {
    $("#files-tree")
      .jstree()
      .delete_node(file.id);
    notify(`File ${file.data.name} successfully deleted.`, "success", 5);
  });
}

function editFile(file) {
  const filepath = file.data.path.replace(/\//g, ">");
  call(`/edit_file/${filepath}`, function(content) {
    openPanel({
      name: "file",
      title: `Edit ${file.data.path}`,
      id: filepath,
      processing: () => {
        const display = document.getElementById(`file_content-${filepath}`);
        // eslint-disable-next-line new-cap
        let fileEditor = (editors[filepath] = CodeMirror.fromTextArea(display, {
          lineWrapping: true,
          lineNumbers: true,
          theme: "cobalt",
          matchBrackets: true,
          mode: "python",
          extraKeys: { "Ctrl-F": "findPersistent" },
          scrollbarStyle: "overlay",
        }));
        fileEditor.setSize("100%", "100%");
        fileEditor.setValue(content);
        fileEditor.refresh();
      }
    });
  })
}

function saveFile(file) {
  $(`[id="file_content-${file}"]`).text(editors[file].getValue());
  fCall(`/save_file/${file}`, `file-content-form-${file}`, function() {
    notify("File successfully saved.", "success", 5);
    $(`[id="file-${file}"`).remove();
  });
}

function showFileUploadPanel(folder) {
  const path = folder.replace(/\//g, ">");
  openPanel({
    name: "upload_files",
    title: `Upload files to ${folder}`,
    id: path,
    processing: () => {
      const element = document.getElementById(`dropzone-${path}`);
      let dropzone = new Dropzone(element, {
        url: "/upload_files",
        autoProcessQueue: false,
      });
      $(`[id="dropzone-submit-${path}"]`).click(function() {
        $(`[id="folder-${path}"]`).val(folder);
        dropzone.processQueue();
        notify("File successfully uploaded.", "success", 5);
        $(`[id="upload_files-${path}"]`).remove();
      });
    }
  });
}

function displayFiles() {
  openPanel({
    name: "files",
    processing: function() {
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
                    onclick='eNMS.administration.editFile(${data})'
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
                    onclick='eNMS.administration.deleteFile(${data})'
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
                onclick="eNMS.administration.showFileUploadPanel('${
                  node.data.path
                }')"
              >
                <span class="glyphicon glyphicon-plus"></span>
              </button>
                </div>
                `);
            }
          },
        },
      });
    }
  });
}

configureNamespace("administration", [
  databaseDeletion,
  deleteFile,
  displayFiles,
  editFile,
  exportTopology,
  getClusterStatus,
  getGitContent,
  importService,
  migrationsExport,
  migrationsImport,
  saveSettings,
  saveFile,
  scanCluster,
  showSettings,
  showFileUploadPanel,
  showImportServicePanel,
  showImportTopologyPanel,
  showMigrationPanel,
]);
