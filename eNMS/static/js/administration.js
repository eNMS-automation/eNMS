/*
global
CodeMirror: false
settings: true
Dropzone: false
JSONEditor: false
*/

import { call, configureNamespace, editors, notify, openPanel } from "./base.js";
import { tables } from "./table.js";

let settingsEditor;

function saveSettings() {
  call({
    url: "/save_settings",
    data: settingsEditor.get(),
    callback: function() {
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
    callback: function() {
      settingsEditor = new JSONEditor(document.getElementById("content"), {}, settings);
    },
  });
}

function getClusterStatus() {
  call({
    url: "/get_cluster_status",
    callback: function() {
      tables["server"].ajax.reload(null, false);
      setTimeout(getClusterStatus, 15000);
    },
  });
}

function migrationsExport() {
  notify("Export initiated.", "success", 5);
  call({
    url: "/migration_export",
    form: "migration-form",
    callback: function() {
      notify("Export successful.", "success", 5);
    },
  });
}

function showMigrationPanel() {
  openPanel({
    name: "database_migration",
    callback: () => {
      call({
        url: "/get_migration_folders",
        callback: function(folders) {
          let list = document.getElementById("versions");
          folders.forEach((item) => {
            let option = document.createElement("option");
            option.textContent = option.value = item;
            list.appendChild(option);
          });
        },
      });
    },
  });
}

function migrationsImport() {
  notify("Import initiated.", "success", 5);
  call({
    url: "/migration_import",
    form: "migration-form",
    callback: function(result) {
      notify(result, "success", 5);
    },
  });
}

function showImportServicePanel() {
  openPanel({
    name: "import_service",
    callback: () => {
      call({
        url: "/get_exported_services",
        callback: function(services) {
          let list = document.getElementById("service");
          services.forEach((item) => {
            let option = document.createElement("option");
            option.textContent = option.value = item;
            list.appendChild(option);
          });
          $("#service").selectpicker("refresh");
        },
      });
    },
  });
}

function importService() {
  call({
    url: `/import_service/${$("#service").val()}`,
    callback: function(result) {
      notify("Import successful.", "success", 5);
      $("#import_service").remove();
    },
  });
}

function databaseDeletion() {
  notify("Starting to delete...", "success", 5);
  call({
    url: "/database_deletion",
    form: "database_deletion-form",
    callback: function(result) {
      notify("Deletion done.", "success", 5);
      $("#deletion-form").remove();
    },
  });
}

function getGitContent() {
  call({
    url: "/get_git_content",
    callback: function(result) {
      notify("Action successful.", "success", 5);
    },
  });
}

function scanCluster() {
  notify("Scan started.", "success", 5);
  call({
    url: "/scan_cluster",
    callback: function(cluster) {
      notify("Scan completed.", "success", 5);
    },
  });
}

function deleteFile(file) {
  call({
    url: `/delete_file/${file.data.path.replace(/\//g, ">")}`,
    callback: function() {
      $("#files-tree")
        .jstree()
        .delete_node(file.id);
      notify(`File ${file.data.name} successfully deleted.`, "success", 5);
    },
  });
}

function editFile(file) {
  const filepath = file.data.path.replace(/\//g, ">");
  call({
    url: `/edit_file/${filepath}`,
    callback: function(content) {
      openPanel({
        name: "file",
        title: `Edit ${file.data.path}`,
        id: filepath,
        callback: () => {
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
        },
      });
    },
  });
}

function saveFile(file) {
  $(`[id="file_content-${file}"]`).text(editors[file].getValue());
  call({
    url: `/save_file/${file}`,
    form: `file-content-form-${file}`,
    callback: function() {
      notify("File successfully saved.", "success", 5);
      $(`[id="file-${file}"`).remove();
    },
  });
}

function createNewFolder() {
  notify("Not implemented yet.", "error", 5);
}

function showFileUploadPanel(folder) {
  const path = folder.replace(/\//g, ">");
  openPanel({
    name: "upload_files",
    title: `Upload files to ${folder}`,
    id: path,
    callback: () => {
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
    },
  });
}

function displayFiles() {
  openPanel({
    name: "files",
    callback: function() {
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
                onclick="eNMS.administration.showFileUploadPanel('${node.data.path}')"
              >
                <span class="glyphicon glyphicon-plus"></span>
              </button>
                </div>
                `);
            }
          },
        },
      });
    },
  });
}

configureNamespace("administration", [
  createNewFolder,
  databaseDeletion,
  deleteFile,
  displayFiles,
  editFile,
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
  showMigrationPanel,
]);
