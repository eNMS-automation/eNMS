/*
global
CodeMirror: false
settings: true
Dropzone: false
*/

import {
  call,
  configureNamespace,
  editors,
  jsonEditors,
  notify,
  openPanel,
} from "./base.js";
import { tables } from "./table.js";

function saveSettings() {
  const newSettings = jsonEditors.settings.get();
  call({
    url: "/save_settings",
    data: {
      settings: newSettings,
      save: $("#write_changes").prop("checked"),
    },
    callback: function () {
      settings = newSettings;
      $("#settings_panel").remove();
      notify("Settings saved.", "success", 5, true);
    },
  });
}

function showSettings() {
  openPanel({
    name: "settings_panel",
    title: "Settings",
    size: "700px 600px",
    callback: function () {
      jsonEditors.settings.set(settings);
    },
  });
}

function getClusterStatus() {
  call({
    url: "/get_cluster_status",
    callback: function () {
      tables.server.table.ajax.reload(null, false);
      setTimeout(getClusterStatus, 15000);
    },
  });
}

function migrationsExport() {
  notify("Migration Export initiated.", "success", 5, true);
  call({
    url: "/migration_export",
    form: "migration-form",
    callback: function () {
      notify("Migration Export successful.", "success", 5, true);
    },
  });
}

function showMigrationPanel() {
  openPanel({
    name: "database_migration",
    title: "Database Migration",
    size: "auto",
    callback: () => {
      call({
        url: "/get_migration_folders",
        callback: function (folders) {
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
  notify("Inventory Import initiated.", "success", 5, true);
  call({
    url: "/migration_import",
    form: "migration-form",
    callback: function (result) {
      notify(result, "success", 5, true);
    },
  });
}

function showImportServicePanel() {
  openPanel({
    name: "import_service",
    title: "Import Service",
    size: "600 300",
    callback: () => {
      call({
        url: "/get_exported_services",
        callback: function (services) {
          let list = document.getElementById("import_services");
          services.forEach((item) => {
            let option = document.createElement("option");
            option.textContent = option.value = item;
            list.appendChild(option);
          });
          $("#import_services").selectpicker("refresh");
        },
      });
    },
  });
}

function importService() {
  call({
    url: `/import_service/${$("#import_services").val()}`,
    title: "Import Service",
    callback: function (result) {
      notify("Service Import successful.", "success", 5, true);
      $("#import_service").remove();
    },
  });
}

function databaseDeletion() {
  notify("Starting Database Deletion", "success", 5, true);
  call({
    url: "/database_deletion",
    title: "Database Deletion",
    form: "database_deletion-form",
    callback: function () {
      notify("Database Deletion done.", "success", 5, true);
      $("#database_deletion").remove();
    },
  });
}

function resultLogDeletion() {
  notify("Log Deletion initiated...", "success", 5, true);
  call({
    url: "/result_log_deletion",
    form: "result_log_deletion-form",
    callback: function () {
      notify("Log Deletion done.", "success", 5, true);
      $("#result_log_deletion").remove();
    },
  });
}

function getGitContent() {
  call({
    url: "/get_git_content",
    callback: function () {
      notify("Successfully pulled content from git.", "success", 5, true);
    },
  });
}

function scanCluster() {
  notify("Cluster Scan initiated...", "success", 5, true);
  call({
    url: "/scan_cluster",
    callback: function () {
      notify("Cluster Scan completed.", "success", 5, true);
    },
  });
}

function deleteFile(file) {
  call({
    url: `/delete_file/${file.data.path.replace(/\//g, ">")}`,
    callback: function () {
      $("#files-tree").jstree().delete_node(file.id);
      notify(`File ${file.data.name} successfully deleted.`, "success", 5, true);
    },
  });
}

function editFile(file) {
  const filepath = file.data.path.replace(/\//g, ">");
  call({
    url: `/edit_file/${filepath}`,
    callback: function (content) {
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
            mode: "python",
            extraKeys: { "Ctrl-F": "findPersistent" },
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
    callback: function () {
      notify(`File ${file} successfully saved.`, "success", 5, true);
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
      $(`[id="dropzone-submit-${path}"]`).click(function () {
        $(`[id="folder-${path}"]`).val(folder);
        dropzone.processQueue();
        notify("Files successfully uploaded.", "success", 5, true);
        $(`[id="upload_files-${path}"]`).remove();
      });
    },
  });
}

function displayFiles() {
  openPanel({
    name: "files",
    title: "Files",
    callback: function () {
      $("#files-tree").jstree({
        core: {
          animation: 200,
          themes: { stripes: true, variant: "large" },
          check_callback: true,
          data: {
            url: function (node) {
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
          default: function (el, node) {
            if (!node) return;
            if (node.type == "file") {
              const data = JSON.stringify(node);
              $(el).find("a").append(`
                <div style="position: absolute; top: 0px; right: 200px">
                  ${node.data.modified}
                </div>
                <div style="position: absolute; top: 0px; right: 50px">
                  <button
                    type="button"
                    class="btn btn-xs btn-primary"
                    onclick='eNMS.administration.editFile(${data})'
                  >
                    <span class="glyphicon glyphicon-edit"></span>
                  </button>
                  <button
                    type="button"
                    class="btn btn-xs btn-info"
                    onclick="location.href='/download_file/${node.data.path}'"
                  >
                    <span class="glyphicon glyphicon-download"></span>
                  </button>
                  <button
                    type="button"
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
                    onclick="eNMS.administration.showFileUploadPanel(
                      '${node.data.path}'
                    )"
                  >
                    <span class="glyphicon glyphicon-plus"></span>
                  </button>
                </div>
                `);
            }
          },
        },
      });
      $("#files-tree").on("ready.jstree", function () {
        $(this).off("click.jstree", ".jstree-anchor");
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
  resultLogDeletion,
  saveSettings,
  saveFile,
  scanCluster,
  showSettings,
  showFileUploadPanel,
  showImportServicePanel,
  showMigrationPanel,
]);
