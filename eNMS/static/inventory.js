/*
global
alertify: false
call: false
CodeMirror: false
config: true
createPanel: false
fCall: false
initSelect: false
initTable: false
openUrl: false
tables: false
*/

// eslint-disable-next-line
function sshConnection(id) {
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
    alertify.notify(link, "success", 15);
    const warning = `Don't forget to turn off the pop-up blocker !`;
    alertify.notify(warning, "error", 20);
    $(`#connection-${id}`).remove();
  });
}

// eslint-disable-next-line
function savePoolObjects(id) {
  fCall(`/save_pool_objects/${id}`, `pool-objects-form-${id}`, function() {
    tables["pool"].ajax.reload(null, false);
    alertify.notify("Changes saved.", "success", 5);
    $(`#pool_objects-${id}`).remove();
  });
}

// eslint-disable-next-line
function showPoolObjectsPanel(id) {
  createPanel("pool_objects", "Pool Objects", id, function() {
    call(`/get/pool/${id}`, function(pool) {
      if (pool.devices.length > 1000 || pool.links.length > 1000) {
        alertify.notify("Too many objects to display.", "error", 5);
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
}

// eslint-disable-next-line
function updatePools(pool) {
  alertify.notify("Update starting...", "success", 5);
  const endpoint = pool ? `/update_pool/${pool}` : "/update_all_pools";
  call(endpoint, function() {
    tables["pool"].ajax.reload(null, false);
    alertify.notify("Update successful.", "success", 5);
  });
}

// eslint-disable-next-line
function showDeviceNetworkData(device) {
  call(`/get_device_network_data/${device.id}`, (result) => {
    if (!result.configuration && !result.operational_data) {
      alertify.notify("No data stored.", "error", 5);
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
}

// eslint-disable-next-line
function showDeviceResultsPanel(device) {
  createPanel("result", `Results - ${device.name}`, null, function() {
    initTable("result", device);
  });
}
