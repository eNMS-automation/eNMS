/*
global
CodeMirror: false
configurationProperties: false
settings: true
echarts: false
theme: false
*/

import { compare } from "./automation.js";
import {
  call,
  configureNamespace,
  downloadFile,
  initSelect,
  notify,
  openPanel,
  openUrl,
} from "./base.js";
import { tables, tableInstances } from "./table.js";

function drawDiagrams(diagram, result) {
  const options = {
    tooltip: {
      formatter: "{b} : {c} ({d}%)",
    },
    series: [
      {
        type: "pie",
        data: result.data,
      },
    ],
    label: {
      normal: {
        formatter: "{b} ({c})",
      },
    },
    ...theme.dashboard,
  };
  if (result.legend.length < 10) {
    if (!options.legend) options.legend = {};
    Object.assign(options.legend, {
      orient: "horizontal",
      bottom: 0,
      data: result.legend,
    });
  }
  diagram.setOption(options);
}

function parseData(data) {
  let result = [];
  let legend = [];
  for (let [key, value] of Object.entries(data)) {
    key = key || "Empty string";
    result.push({
      value: value,
      name: key,
    });
    legend.push(key);
  }
  return { data: result, legend: legend };
}

export function showConnectionPanel(device) {
  openPanel({
    name: "device_connection",
    title: `Connect to ${device.name}`,
    size: "auto",
    id: device.id,
    callback: () => {
      $(`#custom-credentials-${device.id}`).change(function () {
        $(`#credentials-fields-${device.id}`).show();
      });
      $(`#device-credentials-${device.id},#user-credentials-${device.id}`).change(
        function () {
          $(`#credentials-fields-${device.id}`).hide();
        }
      );
    },
  });
}

export function initDashboard() {
  const diagrams = {};
  const defaultProperties = {
    device: "model",
    link: "model",
    user: "name",
    service: "vendor",
    workflow: "vendor",
    task: "status",
  };
  call({
    url: "/count_models",
    callback: function (result) {
      for (const type of Object.keys(defaultProperties)) {
        $(`#count-${type}`).text(result.counters[type]);
      }
      for (const [type, objects] of Object.entries(result.properties)) {
        const diagram = echarts.init(document.getElementById(type));
        drawDiagrams(diagram, parseData(objects));
        diagrams[type] = diagram;
      }
    },
  });

  Object.keys(defaultProperties).forEach((type) => {
    $(`#${type}-properties`)
      .selectpicker()
      .on("change", function () {
        call({
          url: `/counters/${this.value}/${type}`,
          callback: function (objects) {
            drawDiagrams(diagrams[type], parseData(objects));
          },
        });
      });
  });
}

function webConnection(id) {
  call({
    url: `/web_connection/${id}`,
    form: `connection-parameters-form-${id}`,
    callback: function (result) {
      let url = settings.app.address;
      if (!url) {
        url = `${window.location.protocol}//${window.location.hostname}`;
      }
      const link = result.redirection
        ? `${url}/terminal${result.port}/`
        : `${url}:${result.port}`;
      setTimeout(function () {
        openUrl(link);
      }, 300);
      const message = `Click here to connect to ${result.device}.`;
      notify(`<a target='_blank' href='${link}'>${message}</a>`, "success", 15, true);
      const warning = `Don't forget to turn off the pop-up blocker !`;
      notify(warning, "error", 15);
      $(`#connection-${id}`).remove();
    },
  });
}

function desktopConnection(id) {
  notify("Starting SSH connection to the device...", "success", 3, true);
  call({
    url: `/desktop_connection/${id}`,
    form: `connection-parameters-form-${id}`,
    callback: function (result) {
      let loc = window.location;
      if (result.hasOwnProperty("error")) {
        notify(`Error: ${result.error}`, "error", 10, true);
      } else {
        const link = `${result.username}@${loc.hostname}:${result.port}`;
        const message = `Click here to connect to ${result.device_name}.`;
        notify(`<a href='ssh://${link}'>${message}</a>`, "success", 15, true);
      }
    },
  });
}

function savePoolObjects(id) {
  call({
    url: `/save_pool_objects/${id}`,
    form: `pool-objects-form-${id}`,
    callback: function () {
      tableInstances.pool.table.ajax.reload(null, false);
      notify("Changes to pool saved.", "success", 5, true);
      $(`#pool_objects-${id}`).remove();
    },
  });
}

function showPoolObjectsPanel(id) {
  openPanel({
    name: "pool_objects",
    title: "Pool Objects",
    id: id,
    callback: function () {
      call({
        url: `/get/pool/${id}`,
        callback: function (pool) {
          if (pool.devices.length > 1000 || pool.links.length > 1000) {
            notify("Too many objects to display.", "error", 5);
          } else {
            for (const type of ["device", "link"]) {
              initSelect($(`#${type}s-${id}`), type, `pool_objects-${id}`);
              pool[`${type}s`].forEach((o) => {
                $(`#${type}s-${id}`).append(new Option(o.name, o.id));
              });
              $(`#${type}s-${id}`)
                .val(pool[`${type}s`].map((n) => n.id))
                .trigger("change");
            }
          }
        },
      });
    },
  });
}

function updatePools(pool) {
  notify("Pool Update initiated...", "success", 5, true);
  const endpoint = pool ? `/update_pool/${pool}` : "/update_all_pools";
  call({
    url: endpoint,
    callback: function () {
      tableInstances.pool.table.ajax.reload(null, false);
      notify("Pool Update successful.", "success", 5, true);
    },
  });
}

function showSessionLog(sessionId) {
  call({
    url: `/get_session_log/${sessionId}`,
    callback: (log) => {
      if (!log) {
        notify(
          "No log stored (e.g device unreachable or authentication error).",
          "error",
          5,
          true
        );
      } else {
        openPanel({
          name: "session_log",
          content: `<div id="content-${sessionId}" style="height:100%"></div>`,
          title: "Session log",
          id: sessionId,
          callback: function () {
            const content = document.getElementById(`content-${sessionId}`);
            // eslint-disable-next-line new-cap
            const editor = CodeMirror(content, {
              lineWrapping: true,
              lineNumbers: true,
              readOnly: true,
              theme: "cobalt",
              mode: "network",
              extraKeys: { "Ctrl-F": "findPersistent" },
            });
            editor.setSize("100%", "100%");
            editor.setValue(log);
          },
        });
      }
    },
  });
}

function downloadNetworkData(id) {
  downloadFile(
    $(`#data-type-${id}`).val(),
    $(`#content-${id}`).data("CodeMirrorInstance").getValue(),
    "txt"
  );
}

function displayNetworkData(type, id, result, datetime) {
  openPanel({
    name: "device_data",
    content: `
      <div class="modal-body">
        <nav
          class="navbar navbar-default nav-controls"
          role="navigation"
        >
          <select id="data-type-${id}">
            ${Object.entries(configurationProperties).map(
              ([value, name]) => `<option value="${value}">${name}</option>`
            )}
          </select>
          <button
            onclick="eNMS.inventory.downloadNetworkData('${id}')"
            type="button"
            class="btn btn-primary"
            style="margin-left: 10px"
          >
            <span class="glyphicon glyphicon-download"></span>
          </button>
        </nav>
        <div class="x_title">
          <h4 class="text-center" style="color:#FFF">${datetime}</h4>
        </div>
        <div id="content-${id}"></div>
      </div>`,
    title: "Network Data",
    id: id,
    callback: function () {
      $(`#data-type-${id}`).val(type).selectpicker("refresh");
      const content = document.getElementById(`content-${id}`);
      // eslint-disable-next-line new-cap
      const editor = CodeMirror(content, {
        lineWrapping: true,
        lineNumbers: true,
        readOnly: true,
        theme: "cobalt",
        mode: "network",
        extraKeys: { "Ctrl-F": "findPersistent" },
      });
      $(`#content-${id}`).data("CodeMirrorInstance", editor);
      editor.setSize("100%", "100%");
      $(`#data-type-${id}`)
        .on("change", function () {
          editor.setValue(result[this.value]);
          editor.refresh();
        })
        .change();
    },
  });
}

export const showDeviceData = function (device) {
  call({
    url: `/get_device_network_data/${device.id}`,
    callback: (result) => {
      if (Object.keys(configurationProperties).some((p) => result[p])) {
        displayNetworkData("configuration", device.id, result, device.last_runtime);
      } else {
        notify("No data stored.", "error", 5);
      }
    },
  });
};

function showGitConfiguration(device, commit) {
  call({
    url: `/get_git_network_data/${device.name}/${commit.hash}`,
    callback: (result) => {
      const type = $(`#data-type-${device.id}`).val();
      displayNetworkData(type, commit.hash, result, commit.date);
    },
  });
}

function showGitHistory(device) {
  call({
    url: `/get_git_history/${device.id}`,
    callback: (commits) => {
      if (Object.keys(configurationProperties).some((p) => commits[p].length)) {
        openPanel({
          name: "git_history",
          id: device.id,
          title: "Configuration",
          content: `
            <nav
              class="navbar navbar-default nav-controls"
              role="navigation"
              style="margin-top: 5px"
            >
              <select id="data-type-${device.id}">
                ${Object.entries(configurationProperties).map(
                  ([value, name]) => `<option value="${value}">${name}</option>`
                )}
              </select>
              <button
                class="btn btn-info"
                id="compare-${device.id}-btn"
                data-tooltip="Compare"
                type="button"
                style="margin-left:10px"
              >
                <span class="glyphicon glyphicon-adjust"></span>
              </button>
            </nav>
            <div class="modal-body">
              <table 
                id="configuration-table-${device.id}"
                class="table table-striped table-bordered table-hover wrap"
                style="width:100%"
              >
                <thead></thead>
                <tbody></tbody>
              </table>
            <div>`,
          callback: () => {
            $(`#data-type-${device.id}`).selectpicker("refresh");
            let table = $(`#configuration-table-${device.id}`)
              // eslint-disable-next-line new-cap
              .DataTable({
                columns: [
                  { width: "250px", title: "Datetime" },
                  { title: "Commit Hash" },
                  { width: "35px", className: "dt-center" },
                  { width: "30px", title: "V1", className: "dt-center" },
                  { width: "30px", title: "V2", className: "dt-center" },
                ],
              })
              .order([0, "desc"])
              .draw();
            $(`#data-type-${device.id}`)
              .on("change", function () {
                const configurationProperty = this.value;
                table.clear();
                $(`#compare-${device.id}-btn`)
                  .unbind("click")
                  .on("click", function () {
                    compare(configurationProperty, device);
                  });
                commits[configurationProperty].forEach((commit) => {
                  table.row.add([
                    `${commit.date}`,
                    `${commit.hash}`,
                    `<button
                      type="button"
                      class="btn btn-sm btn-info"
                      onclick="eNMS.inventory.showGitConfiguration(
                        ${JSON.stringify(device).replace(/"/g, "'")},
                        ${JSON.stringify(commit).replace(/"/g, "'")}
                      )"
                      data-tooltip="Configuration"
                    >
                      <span class="glyphicon glyphicon-cog"></span>
                    </button>`,
                    `<input
                      type="radio"
                      name="v1-${configurationProperty}-${device.id}"
                      value="${commit.hash}">
                    </input>`,
                    `<input
                      type="radio"
                      name="v2-${configurationProperty}-${device.id}"
                      value="${commit.hash}">
                    </input>`,
                  ]);
                });
                table.draw(false);
              })
              .change();
          },
        });
      } else {
        notify("No data stored.", "error", 5);
      }
    },
  });
}

function showDeviceResultsPanel(device) {
  openPanel({
    name: "table",
    content: `
      <div class="modal-body">
        <div id="tooltip-overlay" class="overlay"></div>
        <form
          id="search-form-device_result-${device.id}"
          class="form-horizontal form-label-left"
          method="post"
        >
          <nav
            id="controls-device_result-${device.id}"
            class="navbar navbar-default nav-controls"
            role="navigation"
          ></nav>
          <table
            id="table-device_result-${device.id}"
            class="table table-striped table-bordered table-hover"
            cellspacing="0"
            width="100%"
          ></table>
        </form>
      </div>`,
    id: device.id,
    type: "device_result",
    title: `Results - ${device.name}`,
    callback: function () {
      // eslint-disable-next-line new-cap
      new tables["device_result"]("device_result", device, null, device.id);
    },
  });
}

function showImportTopologyPanel() {
  openPanel({
    name: "excel_import",
    title: "Import Topology as an Excel file",
    callback: () => {
      document.getElementById("file").onchange = function () {
        importTopology();
      };
    },
  });
}

function exportTopology() {
  notify("Topology export starting...", "success", 5, true);
  call({
    url: "/export_topology",
    form: "excel_export-form",
    callback: function () {
      notify("Topology successfully exported.", "success", 5, true);
    },
  });
}

function importTopology() {
  notify("Topology import: starting...", "success", 5, true);
  const formData = new FormData($("#import-form")[0]);
  $.ajax({
    type: "POST",
    url: "/import_topology",
    dataType: "json",
    data: formData,
    contentType: false,
    processData: false,
    async: true,
    success: function (result) {
      notify(result, "success", 5, true);
    },
  });
}

configureNamespace("inventory", [
  downloadNetworkData,
  exportTopology,
  desktopConnection,
  showConnectionPanel,
  webConnection,
  savePoolObjects,
  showPoolObjectsPanel,
  updatePools,
  showGitHistory,
  showDeviceData,
  showDeviceResultsPanel,
  showGitConfiguration,
  showImportTopologyPanel,
  showSessionLog,
]);
