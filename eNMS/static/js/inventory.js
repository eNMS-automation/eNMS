/*
global
CodeMirror: false
settings: true
echarts: false
initSelect: false
*/

import {
  call,
  configureNamespace,
  fCall,
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

export function showConnectionPanel(id) {
  openPanel({
    name: "device_connection",
    id: id,
    processing: () => {
      $(`#custom-credentials-${id}`).change(function() {
        $(`#credentials-fields-${id}`).show();
      });
      $(`#device-credentials-${id},#user-credentials-${id}`).change(function() {
        $(`#credentials-fields-${id}`).hide();
      });
    }
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
  call("/count_models", function(result) {
    for (const type of Object.keys(defaultProperties)) {
      $(`#count-${type}`).text(result.counters[type]);
    }
    for (const [type, objects] of Object.entries(result.properties)) {
      const diagram = echarts.init(document.getElementById(type));
      drawDiagrams(diagram, parseData(objects));
      diagrams[type] = diagram;
    }
  });

  $.each(defaultProperties, function(type) {
    $(`#${type}-properties`)
      .selectpicker()
      .on("change", function() {
        call(`/counters/${this.value}/${type}`, function(objects) {
          drawDiagrams(diagrams[type], parseData(objects));
        });
      });
  });
}

function sshConnection(id) {
  fCall(`/connection/${id}`, `connection-parameters-form-${id}`, function(
    result
  ) {
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
  });
}

// eslint-disable-next-line
function handOffSSHConnection(id) {
  fCall(`/handoffssh/${id}`, `connection-parameters-form-${id}`, function(
    result
  ) {
    let url = settings.app.address;
    if (!url) {
      url = `${window.location.protocol}//${window.location.host}`;
    }
    const link = `${result.username}@${window.location.hostname}:${
      result.port
    }`;
    const message = `Click here to connect to ${result.device_name}.`;
    notify(`<a href='ssh://${link}'>${message}</a>`, "success", 15);
  });
}

// eslint-disable-next-line
function savePoolObjects(id) {
  fCall(`/save_pool_objects/${id}`, `pool-objects-form-${id}`, function() {
    tables["pool"].ajax.reload(null, false);
    notify("Changes saved.", "success", 5);
    $(`#pool_objects-${id}`).remove();
  });
}

function showPoolObjectsPanel(id) {
  openPanel({
    name: "pool_objects",
    title: "Pool Objects",
    id: id,
    processing: function() {
      call(`/get/pool/${id}`, function(pool) {
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
      });
    }
  });
}

function updatePools(pool) {
  notify("Update starting...", "success", 5);
  const endpoint = pool ? `/update_pool/${pool}` : "/update_all_pools";
  call(endpoint, function() {
    tables["pool"].ajax.reload(null, false);
    notify("Update successful.", "success", 5);
  });
}

export const showDeviceData = function(device) {
  call(`/get_device_network_data/${device.id}`, (result) => {
    if (!result.configuration && !result.operational_data) {
      notify("No data stored.", "error", 5);
    } else {
      openPanel({
        name: "device_data",
        title: `Device Data - ${device.name}`,
        id: device.id,
        processing: function() {
          const content = document.getElementById(`content-${device.id}`);
          // eslint-disable-next-line new-cap
          const editor = CodeMirror(content, {
            lineWrapping: true,
            lineNumbers: true,
            readOnly: true,
            theme: "cobalt",
            extraKeys: { "Ctrl-F": "findPersistent" },
            scrollbarStyle: "overlay",
          });
          editor.setSize("100%", "100%");
          $(`#data_type-${device.id}`)
            .on("change", function() {
              editor.setValue(result[this.value]);
            })
            .change();
        }
      });
    }
  });
};

function showSessionLog(sessionId) {
  call(`/get_session_log/${sessionId}`, (log) => {
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
        processing: function() {
          const content = document.getElementById(`content-${sessionId}`);
          // eslint-disable-next-line new-cap
          const editor = CodeMirror(content, {
            lineWrapping: true,
            lineNumbers: true,
            readOnly: true,
            theme: "cobalt",
            extraKeys: { "Ctrl-F": "findPersistent" },
            scrollbarStyle: "overlay",
          });
          editor.setSize("100%", "100%");
          editor.setValue(log);
        }
      });
    }
  });
}

function showDeviceResultsPanel(device) {
  openPanel({
    name: "result_table",
    title: `Results - ${device.name}`,
    processing: function() {
      initTable("result", device, null, "table-result");
    }
  });
}

configureNamespace("inventory", [
  handOffSSHConnection,
  showConnectionPanel,
  sshConnection,
  savePoolObjects,
  showPoolObjectsPanel,
  updatePools,
  showDeviceData,
  showDeviceResultsPanel,
  showSessionLog,
]);
