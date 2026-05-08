/*
global
CodeMirror: false
page: false
settings: true
Dropzone: false
rbac: false
user: false
*/

import {
  call,
  configureNamespace,
  displayDiff,
  downloadFile,
  editors,
  initCodeMirror,
  notify,
  openPanel,
  processInstance,
} from "./base.js";
import { clearSearch, refreshTable, tables } from "./table.js";

export let folderPath = localStorage.getItem("folderPath") || "";
export let currentStore;

function displayFiles() {
  if ($("#files").length || page == "file_table") {
    return notify("The files table is already displayed.", "error", 5);
  }
  openPanel({
    name: "files",
    size: "1000 600",
    content: `
      <form id="search-form-file" style="margin: 15px">
        <div id="tooltip-overlay" class="overlay"></div>
        <nav
          id="controls-file"
          class="navbar navbar-default nav-controls"
          role="navigation"
        ></nav>
        <table
          id="table-file"
          style="margin-top: 10px;"
          class="table table-striped table-bordered table-hover"
          cellspacing="0"
          width="100%"
        ></table>
      </form>`,
    tableId: "file",
    title: "Files",
    callback: function() {
      // eslint-disable-next-line new-cap
      new tables["file"]();
    },
  });
}

export function displayFolderPath() {
  let currentPath = "";
  let htmlPath = [];
  `/files${folderPath}`
    .split("/")
    .slice(1)
    .forEach((folder) => {
      currentPath += folder == "files" ? "" : `/${folder}`;
      htmlPath.push(`<b> / </b>
        <button type="button" class="btn btn-xs btn-primary"
        onclick="eNMS.administration.enterFolder({path: '${currentPath}'})">
          ${folder}
        </button>
      `);
    });
  $("#current-folder-path").html(`<b>Current Folder :</b>${htmlPath.join("")}`);
}

function enterFolder({ folder, path, parent }) {
  if (!(($("#parent-filtering").val() || "true") == "true")) {
    return notify("Path only valid in 'Hierarchical Display' mode.", "warning", 5);
  }
  clearSearch("file");
  if (parent) {
    folderPath = folderPath
      .split("/")
      .slice(0, -1)
      .join("/");
  } else {
    folderPath = path || folder ? path || `${folderPath}/${folder}` : "";
  }
  localStorage.setItem("folderPath", folderPath);
  refreshTable("file", null, null, true);
  if (folder) {
    $("#upward-folder-btn").removeClass("disabled");
  } else if (!folderPath) {
    $("#upward-folder-btn").addClass("disabled");
  }
  displayFolderPath();
}

function enterStore(data) {
  call({
    url: "/get_store",
    data: { store: currentStore, ...data },
    callback: function(store) {
      currentStore = store;
      if (store) {
        $("#upward-store-btn").removeClass("disabled");
      } else {
        $("#upward-store-btn").addClass("disabled");
      }
      const tableId = store ? `${store.data_type}-${store.id}` : "store";
      $("#table-div").empty().html(`
        <form id="search-form-${tableId}"
          style="padding: 12px 17px; width: 100%">
          <div id="tooltip-overlay" class="overlay"></div>
          <nav
            id="controls-${tableId}"
            class="navbar navbar-default nav-controls"
            role="navigation"
          ></nav>
          <table
            id="table-${tableId}"
            style="margin-top: 10px"
            class="table table-striped table-bordered table-hover add-id"
            cellspacing="0"
            width="100%"
          ></table>
        </form>
      `);
      if (store) {
        new tables[store.data_type](store.id, {
          store_id: store.id,
          store_id_filter: "equality",
        });
      } else {
        new tables["store"]();
      }
    },
  });
}

export function displayStorePath() {
  let currentPath = "";
  let htmlPath = [];
  if (!currentStore) return;
  `Data Store${currentStore.path}`.split("/").forEach((store) => {
    currentPath += store == "Data Store" ? "" : `/${store}`;
    htmlPath.push(`<b> / </b>
        <button type="button" class="btn btn-xs btn-primary"
        onclick="eNMS.administration.enterStore({path: '${currentPath}'})">
          ${store}
        </button>
      `);
  });
  $("#current-store-path").html(`<b>Current Store :</b>${htmlPath.join("")}`);
}

function showChangelogDiff(id) {
  call({
    url: `/get_changelog_history/${id}`,
    callback: function(changelog) {
      if (changelog?.history?.properties) {
        displayDiff("changelog", id, changelog.history.properties);
      } else {
        openPanel({
          name: "changelog_diff",
          content: `
            <div class="modal-body">
              <div id="changelog-content-${id}" style="margin-top: 30px"></div>
            </div>`,
          title: "Result",
          id: id,
          callback: function() {
            const editor = initCodeMirror(`changelog-content-${id}`, "network");
            editor.setValue(changelog.content);
            editor.refresh();
          },
        });
      }
    },
  });
}

export function openDebugPanel() {
  openPanel({
    name: "debug",
    title: "Debug Panel",
    size: "1200px 450px",
  });
}

function runDebugCode(snippetId) {
  call({
    url: `/run_debug_code${snippetId ? `/${snippetId}` : ""}`,
    form: "debug-form",
    callback: function(result) {
      if (!snippetId) {
        $("#debug-output").val(result);
      } else if (result.trim()) {
        openPanel({
          name: "snippet-code",
          content: `<div class="modal-body"><div id="debug-${snippetId}"></div></div>`,
          size: "900 500",
          title: "Debug Panel",
          id: snippetId,
          callback: function() {
            const editor = initCodeMirror(`debug-${snippetId}`, "logs");
            editor.setValue(result);
          },
        });
      }
      notify("Code executed successfully.", "success", 5, true);
    },
  });
}

function getClusterStatus() {
  call({
    url: "/get_cluster_status",
    callback: function() {
      refreshTable("server");
      setTimeout(getClusterStatus, 15000);
    },
  });
}

function migrationsExport(type) {
  notify("Migration Export initiated.", "success", 5, true);
  call({
    url: `/${type}_migration_export`,
    form: `${type}-migration-form`,
    callback: function() {
      notify("Migration Export successful.", "success", 5, true);
    },
  });
}

function scanFolder() {
  call({
    url: `/scan_folder/${folderPath.replace(/\//g, ">")}`,
    callback: function() {
      refreshTable("file");
      notify("Scan successful.", "success", 5, true);
    },
  });
}

function editFile(id, filename, filepath) {
  call({
    url: `/edit_file/${filename}`,
    callback: function(content) {
      if (content.error) {
        refreshTable("file");
        return notify(content.error, "error", 5);
      }
      openPanel({
        name: "file_editor",
        title: `Edit ${filepath}`,
        id: id,
        callback: () => {
          const display = document.getElementById(`file_content-${id}`);
          // eslint-disable-next-line new-cap
          let fileEditor = (editors[id] = CodeMirror.fromTextArea(display, {
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
    callback: function() {
      notify("File successfully saved.", "success", 5, true);
      $(`[id="file_editor-${file}"`).remove();
      refreshTable("file");
    },
  });
}

function showFileUploadPanel(folder) {
  if (!folder) folder = folderPath;
  const pathId = folder.replace(/\//g, "-") || 1;
  openPanel({
    name: "upload_files",
    title: `Upload files to ${folder}`,
    size: "700 615",
    id: pathId,
    callback: () => {
      const element = document.getElementById(`dropzone-${pathId}`);
      let dropzone = new Dropzone(element, {
        url: "/upload_files",
        autoProcessQueue: false,
        addRemoveLinks: true,
        parallelUploads: 10,
        queuecomplete: () => {
          $(".dz-remove").remove();
          notify("Files successfully uploaded.", "success", 5, true);
          setTimeout(() => refreshTable("file"), 500);
        },
        init: function() {
          this.on("addedfile", function(file) {
            if (dropzone.files.slice(0, -1).some((f) => f.name == file.name)) {
              notify("There is already a file with the same name.", "error", 5);
              dropzone.removeFile(file);
            }
          });
        },
        timeout: settings.files.upload_timeout,
      });
      $(`[id="dropzone-submit-${pathId}"]`).click(function() {
        $(`[id="folder-${pathId}"]`).val(folder);
        dropzone.processQueue();
      });
    },
  });
}

export function showFolderPanel(id) {
  if (id) return;
  $(`#folder-path`).prop("readonly", true);
  $(`#folder-filename`).prop("readonly", false);
}

export function showStorePanel(id) {
  if (id) {
    $(`#store-data_type-${id}`)
      .prop("disabled", true)
      .selectpicker("refresh");
  } else {
    $("#store-scoped_name").prop("readonly", false);
    $("#store-path").prop("readonly", true);
  }
}

function saveProfile() {
  call({
    url: "/save_profile",
    form: `profile-form-${user.id}`,
    callback: function() {
      notify("Profile saved.", "success", 5, true);
      $(`#profile-${user.id}`).remove();
    },
  });
}

export function showCredentialPanel(id) {
  const postfix = id ? `-${id}` : "";
  $(`#credential-subtype${postfix}`)
    .change(function() {
      if (this.value == "password") {
        $(`#credential-private_key-div${postfix}`).hide();
        $(`#credential-password-div${postfix}`).show();
      } else {
        $(`#credential-password-div${postfix}`).hide();
        $(`#credential-private_key-div${postfix}`).show();
      }
    })
    .trigger("change");
}

function showServerTime() {
  call({
    url: "/get_time",
    callback: function(time) {
      $("#server-time").html(`Server Time: ${time}`);
    },
  });
}

function updateDeviceRbac() {
  notify("RBAC Update Initiated.", "success", 5, true);
  call({
    url: "/update_device_rbac",
    callback: function() {
      notify("RBAC Update successful", "success", 5, true);
    },
  });
}

configureNamespace("administration", [
  displayFiles,
  editFile,
  enterFolder,
  enterStore,
  getClusterStatus,
  migrationsExport,
  openDebugPanel,
  runDebugCode,
  saveFile,
  saveProfile,
  scanFolder,
  showChangelogDiff,
  showFileUploadPanel,
  showServerTime,
  updateDeviceRbac,
]);
