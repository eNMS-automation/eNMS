/*
global
CodeMirror: false
config: true
echarts: false
initSelect: false
*/

import {
  adjustHeight,
  call,
  createPanel,
  fCall,
  notify,
  openUrl,
} from "./base.js";
import { initTable, tables } from "./table.js";

let ns = (window.eNMS.inventory = {});

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
    adjustHeight();
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

ns.sshConnection = function(id) {
  fCall(`/connection/${id}`, `connection-parameters-form-${id}`, function(
    result
  ) {
    let url = config.app.address;
    if (!url) {
      url = `${window.location.protocol}//${window.location.hostname}`;
    }
    const terminal = result.redirection
      ? `${url}/terminal${result.port}/`
      : `${url}:${result.port}`;
    setTimeout(function() {
      openUrl(terminal);
    }, 300);
    const messageLink = `Click here to connect to ${result.device}.`;
    const link = `<a target='_blank' href='${terminal}'>${messageLink}</a>`;
    notify(link, "success", 15);
    const warning = `Don't forget to turn off the pop-up blocker !`;
    notify(warning, "error", 20);
    $(`#connection-${id}`).remove();
  });
};

ns.savePoolObjects = function(id) {
  fCall(`/save_pool_objects/${id}`, `pool-objects-form-${id}`, function() {
    tables["pool"].ajax.reload(null, false);
    notify("Changes saved.", "success", 5);
    $(`#pool_objects-${id}`).remove();
  });
};

ns.showPoolObjectsPanel = function(id) {
  createPanel("pool_objects", "Pool Objects", id, function() {
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
  });
};

ns.updatePools = function(pool) {
  notify("Update starting...", "success", 5);
  const endpoint = pool ? `/update_pool/${pool}` : "/update_all_pools";
  call(endpoint, function() {
    tables["pool"].ajax.reload(null, false);
    notify("Update successful.", "success", 5);
  });
};

export const showDeviceData = (ns.showDeviceData = function(device) {
  call(`/get_device_network_data/${device.id}`, (result) => {
    if (!result.configuration && !result.operational_data) {
      notify("No data stored.", "error", 5);
    } else {
      createPanel(
        "device_data",
        `Device Data - ${device.name}`,
        device.id,
        function() {
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
      );
    }
  });
});

ns.showDeviceResultsPanel = function(device) {
  createPanel("result", `Results - ${device.name}`, null, function() {
    initTable("result", device);
  });
};
