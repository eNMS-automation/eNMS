/*
global
alertify: false
CodeMirror: false
config: true
Dropzone: false
folders: false
JSONEditor: false
*/

import {
  call,
  createPanel,
  editors,
  fCall,
  notify,
  showPanel,
} from "./base.js";
import { tables } from "./table.js";

let configurationEditor;
let administrationNamespace = (window.eNMS.administration = {});

administrationNamespace.showImportTopologyPanel = function() {
  createPanel("excel_import", "Import Topology as an Excel file", 0, () => {
    document.getElementById("file").onchange = function() {
      administrationNamespace.importTopology();
    };
  });
};

administrationNamespace.queryLibreNMS = function() {
  call("/query_librenms", function() {
    notify("Topology imported from LibreNMS.", "success", 5);
  });
};

administrationNamespace.saveConfiguration = function() {
  $.ajax({
    type: "POST",
    url: "/save_configuration",
    contentType: "application/json",
    data: JSON.stringify(configurationEditor.get()),
    success: function() {
      config = configurationEditor.get();
      $("#configuration").remove();
      notify("Configuration saved.", "success", 5);
    },
  });
};

administrationNamespace.showConfiguration = function() {
  createPanel("configuration", "Configuration", null, function() {
    configurationEditor = new JSONEditor(
      document.getElementById("content"),
      {},
      config
    );
  });
};

administrationNamespace.exportTopology = function() {
  notify("Topology export starting...", "success", 5);
  fCall("/export_topology", "excel_export-form", function() {
    notify("Topology successfully exported.", "success", 5);
  });
};

administrationNamespace.importTopology = function() {
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
};

administrationNamespace.getClusterStatus = function() {
  call("/get_cluster_status", function() {
    tables["server"].ajax.reload(null, false);
    setTimeout(administrationNamespace.getClusterStatus, 15000);
  });
};

administrationNamespace.migrationsExport = function() {
  notify("Export initiated.", "success", 5);
  fCall("/migration_export", "migration-form", function() {
    notify("Export successful.", "success", 5);
  });
};

administrationNamespace.showMigrationPanel = function() {
  showPanel("database_migration", null, () => {
    let list = document.getElementById("versions");
    folders.forEach((item) => {
      let option = document.createElement("option");
      option.textContent = option.value = item;
      list.appendChild(option);
    });
  });
};

administrationNamespace.migrationsImport = function() {
  notify("Import initiated.", "success", 5);
  fCall("/migration_import", "migration-form", function(result) {
    notify(result, "success", 5);
  });
};

administrationNamespace.refreshExportedServices = function() {
  call("/get_exported_services", function(services) {
    let list = document.getElementById("service");
    services.forEach((item) => {
      let option = document.createElement("option");
      option.textContent = option.value = item;
      list.appendChild(option);
    });
    $("#service").selectpicker("refresh");
  });
};

administrationNamespace.showImportServicePanel = function() {
  showPanel("import_service", null, () => {
    administrationNamespace.refreshExportedServices();
  });
};

administrationNamespace.importService = function() {
  call(`/import_service/${$("#service").val()}`, function(result) {
    notify("Import successful.", "success", 5);
    $("#import_service").remove();
  });
};

administrationNamespace.databaseDeletion = function() {
  notify("Starting to delete...", "success", 5);
  fCall("/database_deletion", "database_deletion-form", function(result) {
    notify("Deletion done.", "success", 5);
    $("#deletion-form").remove();
  });
};

administrationNamespace.getGitContent = function() {
  call("/get_git_content", function(result) {
    notify("Action successful.", "success", 5);
  });
};

administrationNamespace.scanCluster = function() {
  notify("Scan started.", "success", 5);
  call("/scan_cluster", function(cluster) {
    notify("Scan completed.", "success", 5);
  });
};

administrationNamespace.deleteFile = function(file) {
  call(`/delete_file/${file.data.path.replace(/\//g, ">")}`, function() {
    $("#files-tree")
      .jstree()
      .delete_node(file.id);
    notify(`File ${file.data.name} successfully deleted.`, "success", 5);
  });
};

administrationNamespace.editFile = function(file) {
  const filepath = file.data.path.replace(/\//g, ">");
  call(`/edit_file/${filepath}`, function(content) {
    createPanel("file", `Edit ${file.data.path}`, filepath, () => {
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
    });
  });
};

administrationNamespace.saveFile = function(file) {
  $(`[id="file_content-${file}"]`).text(editors[file].getValue());
  fCall(`/save_file/${file}`, `file-content-form-${file}`, function() {
    notify("File successfully saved.", "success", 5);
    $(`[id="file-${file}"`).remove();
  });
};

administrationNamespace.showFileUploadPanel = function(folder) {
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
      notify("File successfully uploaded.", "success", 5);
      $(`[id="upload_files-${path}"]`).remove();
    });
  });
};

administrationNamespace.createNewFolder = function() {};

administrationNamespace.displayFiles = function() {
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
  });
};
