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
  editors,
  notify,
  openPanel,
  processInstance,
} from "./base.js";
import { refreshTable, tables } from "./table.js";

export let folderPath = localStorage.getItem("folderPath") || "";

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

export function openDebugPanel() {
  openPanel({
    name: "debug",
    title: "Debug Panel",
    size: "1200px 500px",
    callback: function() {
      call({
        url: "/load_debug_snippets",
        callback: function(snippets) {
          for (const name of Object.keys(snippets)) {
            $("#debug-snippets").append(`<option value="${name}">${name}</option>`);
          }
          $("#debug-snippets")
            .val("empty.py")
            .on("change", function() {
              const value = snippets[this.value];
              editors[undefined]["code"].setValue(value);
            })
            .selectpicker("refresh");
        },
      });
    },
  });
}

function runDebugCode() {
  call({
    url: "/run_debug_code",
    form: "debug-form",
    callback: function(result) {
      $("#debug-output").val(result);
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

function migrationsExport() {
  notify("Migration Export initiated.", "success", 5, true);
  call({
    url: "/migration_export",
    form: "migration-form",
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

function showMigrationPanel() {
  openPanel({
    name: "database_migration",
    title: "Database Migration",
    size: "auto",
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
  notify("Inventory Import initiated.", "success", 5, true);
  call({
    url: "/migration_import",
    form: "migration-form",
    callback: function(result) {
      notify(result, "success", 5, true);
    },
  });
}

function databaseDeletion() {
  notify("Starting Database Deletion", "success", 5, true);
  call({
    url: "/database_deletion",
    title: "Database Deletion",
    form: "database_deletion-form",
    callback: function() {
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
    callback: function() {
      notify("Log Deletion done.", "success", 5, true);
      $("#result_log_deletion").remove();
    },
  });
}

function getGitContent() {
  call({
    url: "/get_git_content",
    callback: function() {
      notify("Successfully pulled content from git.", "success", 5, true);
    },
  });
}

function scanCluster() {
  notify("Cluster Scan initiated...", "success", 5, true);
  call({
    url: "/scan_cluster",
    callback: function() {
      notify("Cluster Scan completed.", "success", 5, true);
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
          let fileEditor = (editors[filename] = CodeMirror.fromTextArea(display, {
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
      notify(`File ${file} successfully saved.`, "success", 5, true);
      $(`[id="file_editor-${file}"`).remove();
      refreshTable("file");
    },
  });
}

function showFileUploadPanel(folder) {
  if (!folder) folder = folderPath;
  const pathId = folder.replace(/\//g, ">") || 1;
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

function showProfile() {
  openPanel({
    name: "profile",
    size: "800 auto",
    title: "Profile",
    id: user.id,
    callback: () => {
      call({
        url: `/get/user/${user.id}`,
        data: { properties_only: true },
        callback: function(user) {
          for (const [page, endpoint] of Object.entries(rbac.all_pages)) {
            if (!user.is_admin && !user.pages.includes(page)) continue;
            const option = `<option value='${endpoint}'>${page}</option>`;
            $(`#profile-landing_page-${user.id}`).append(option);
          }
          $(`#profile-landing_page-${user.id}`)
            .val(user.landing_page)
            .selectpicker("refresh");
          processInstance("profile", user);
        },
      });
    },
  });
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
  databaseDeletion,
  displayFiles,
  editFile,
  enterFolder,
  getClusterStatus,
  getGitContent,
  migrationsExport,
  migrationsImport,
  resultLogDeletion,
  runDebugCode,
  saveFile,
  saveProfile,
  scanCluster,
  scanFolder,
  showFileUploadPanel,
  showMigrationPanel,
  showProfile,
  updateDeviceRbac,
]);
