/*
global
CodeMirror: false
settings: true
echarts: false
*/

import {
  call,
  configureNamespace,
  initSelect,
  notify,
  openPanel,
  openUrl,
} from "./base.js";
import { initTable, tables } from "./table.js";

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
  };
  if (result.legend.length < 10) {
    options.legend = {
      orient: "horizontal",
      bottom: 0,
      data: result.legend,
    };
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
      $(`#custom-credentials-${device.id}`).change(function() {
        $(`#credentials-fields-${device.id}`).show();
      });
      $(`#device-credentials-${device.id},#user-credentials-${device.id}`).change(
        function() {
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
    callback: function(result) {
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

  $.each(defaultProperties, function(type) {
    $(`#${type}-properties`)
      .selectpicker()
      .on("change", function() {
        call({
          url: `/counters/${this.value}/${type}`,
          callback: function(objects) {
            drawDiagrams(diagrams[type], parseData(objects));
          },
        });
      });
  });
}

function sshConnection(id) {
  call({
    url: `/connection/${id}`,
    form: `connection-parameters-form-${id}`,
    callback: function(result) {
      let url = settings.app.address;
      if (!url) {
        url = `${window.location.protocol}//${window.location.hostname}`;
      }
      const link = result.redirection
        ? `${url}/terminal${result.port}/`
        : `${url}:${result.port}`;
      setTimeout(function() {
        openUrl(link);
      }, 300);
      const message = `Click here to connect to ${result.device}.`;
      notify(`<a target='_blank' href='${link}'>${message}</a>`, "success", 15);
      const warning = `Don't forget to turn off the pop-up blocker !`;
      notify(warning, "error", 15);
      $(`#connection-${id}`).remove();
    },
  });
}

// eslint-disable-next-line
function handOffSSHConnection(id) {
  notify("Starting SSH connection to the device...", "success", 3);
  call({
    url: `/handoffssh/${id}`,
    form: `connection-parameters-form-${id}`,
    callback: function(result) {
      let loc = window.location;
      if (result.hasOwnProperty("error")) {
        notify(`Error: ${result.error}`, "error", 10);
      } else {
        const link = `${result.username}@${loc.hostname}:${result.port}`;
        const message = `Click here to connect to ${result.device_name}.`;
        notify(`<a href='ssh://${link}'>${message}</a>`, "success", 15);
      }
    },
  });
}

// eslint-disable-next-line
function savePoolObjects(id) {
  call({
    url: `/save_pool_objects/${id}`,
    form: `pool-objects-form-${id}`,
    callback: function() {
      tables["pool"].ajax.reload(null, false);
      notify("Changes saved.", "success", 5);
      $(`#pool_objects-${id}`).remove();
    },
  });
}

function showPoolObjectsPanel(id) {
  openPanel({
    name: "pool_objects",
    title: "Pool Objects",
    id: id,
    callback: function() {
      call({
        url: `/get/pool/${id}`,
        callback: function(pool) {
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
  notify("Update starting...", "success", 5);
  const endpoint = pool ? `/update_pool/${pool}` : "/update_all_pools";
  call({
    url: endpoint,
    callback: function() {
      tables["pool"].ajax.reload(null, false);
      notify("Update successful.", "success", 5);
    },
  });
}

export const showDeviceData = function(device) {
  call({
    url: `/get_device_network_data/${device.id}`,
    callback: (result) => {
      if (!result.configuration && !result.operational_data) {
        notify("No data stored.", "error", 5);
      } else {
        openPanel({
          name: "device_data",
          title: `Device Data - ${device.name}`,
          id: device.id,
          callback: function() {
            const content = document.getElementById(`content-${device.id}`);
            // eslint-disable-next-line new-cap
            const editor = CodeMirror(content, {
              lineWrapping: true,
              lineNumbers: true,
              readOnly: true,
              theme: "cobalt",
              mode: null,
              extraKeys: { "Ctrl-F": "findPersistent" },
              scrollbarStyle: "overlay",
            });
            editor.setSize("100%", "100%");
            $(`#data_type-${device.id}`)
              .on("change", function() {
                editor.setValue(result[this.value]);
                editor.refresh();
              })
              .change();
          },
        });
      }
    },
  });
};

function showSessionLog(sessionId) {
  call({
    url: `/get_session_log/${sessionId}`,
    callback: (log) => {
      if (!log) {
        notify(
          "No log stored (e.g device unreachable or authentication error).",
          "error",
          5
        );
      } else {
        openPanel({
          name: "display",
          title: "Session log",
          id: sessionId,
          callback: function() {
            const content = document.getElementById(`content-${sessionId}`);
            // eslint-disable-next-line new-cap
            const editor = CodeMirror(content, {
              lineWrapping: true,
              lineNumbers: true,
              readOnly: true,
              theme: "cobalt",
              mode: null,
              extraKeys: { "Ctrl-F": "findPersistent" },
              scrollbarStyle: "overlay",
            });
            editor.setSize("100%", "100%");
            editor.setValue(log);
          },
        });
      }
    },
  });
}

function showConfigurationHistory(device) {
  call({
    url: `/get_configuration_history/${device.id}`,
    callback: (commits) => {
      if (!commits.length) {
        notify("No configuration stored.", "error", 5);
      } else {
        commits = commits.map((commit) => `
            <tr>
            <td>${commit.date}</td>
            <td>${commit.hash}</td>
            <td>
              <button type="button" class="btn btn-sm btn-info"
              onclick="eNMS.inventory.showDeviceData(${commit})"
              data-tooltip="Network Data"
                ><span class="glyphicon glyphicon-cog"></span
              ></button>
            </td>
            <td><input type="radio" name="v1-${device.id}" value="${device.id}"></input></td>
            <td><input type="radio" name="v2-${device.id}" value="${device.id}"></input></td>
          </tr>`);
        openPanel({
          name: "display",
          title: "Configuration",
          content: `
            <div class="modal-body">
              <table 
                id="configuration-table-${device.id}"
                class="table table-striped table-bordered table-hover wrap"
                style="width:100%"
              >
                <thead>
                </thead>
                <tbody>
                ${commits.join("")}
                </tbody>
              </table>
            <div>
          `,
          callback: () => {
            $(`#configuration-table-${device.id}`)
              // eslint-disable-next-line new-cap
              .DataTable({
                columns: [
                  { width: "300px", title: "Datetime" },
                  { title: "Commit Hash" },
                  { width: "35px", className: "dt-center" },
                  { width: "30px", title: "V1", className: "dt-center" },
                  { width: "30px", title: "V2", className: "dt-center" },
                ],
              })
              .order([0, "desc"])
              .draw();
          },
        });
      }
    },
  });
}

function showDeviceResultsPanel(device) {
  openPanel({
    name: "table",
    id: device.id,
    type: "device_result",
    title: `Results - ${device.name}`,
    callback: function() {
      initTable("device_result", device, null, device.id);
    },
  });
}

function showImportTopologyPanel() {
  openPanel({
    name: "excel_import",
    title: "Import Topology as an Excel file",
    callback: () => {
      document.getElementById("file").onchange = function() {
        importTopology();
      };
    },
  });
}

function exportTopology() {
  notify("Topology export starting...", "success", 5);
  call({
    url: "/export_topology",
    form: "excel_export-form",
    callback: function() {
      notify("Topology successfully exported.", "success", 5);
    },
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
}

configureNamespace("inventory", [
  exportTopology,
  handOffSSHConnection,
  showConnectionPanel,
  sshConnection,
  savePoolObjects,
  showPoolObjectsPanel,
  updatePools,
  showConfigurationHistory,
  showDeviceData,
  showDeviceResultsPanel,
  showImportTopologyPanel,
  showSessionLog,
]);
