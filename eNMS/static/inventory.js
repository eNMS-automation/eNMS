/*
global
action: false
alertify: false
call: false
createPanel: false
fCall: false
initSelect: false
initTable: false
openUrl: false
showPanel: false
showTypePanel: false
tables: false
*/

// eslint-disable-next-line
function sshConnection(id) {
  fCall(`/connection/${id}`, `#connection-parameters-form-${id}`, function(
    result
  ) {
    let url = result.server_addr;
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
  fCall(`/save_pool_objects/${id}`, `#pool-objects-form-${id}`, function() {
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
function showDeviceConfiguration(device) {
  createPanel(
    "display_configuration",
    `Configuration - ${device.name}`,
    device.id,
    function() {
      call(`/get_device_configuration/${device.id}`, (config) => {
        $(`#content-${device.id}`).html(
          `<pre style="height:100%">${config}</pre>`
        );
      });
    }
  );
}

// eslint-disable-next-line
function showDeviceResultsPanel(device) {
  createPanel("result", `Results - ${device.name}`, null, function() {
    initTable("result", device);
  });
}

// eslint-disable-next-line
function showConfigurationsPanel(device) {
  createPanel(
    "configuration",
    `Configuration - ${device.name}`,
    null,
    function() {
      initTable("configuration", device);
    }
  );
}

// eslint-disable-next-line
function copyResultsToClipboard(id) {
  let node = document.getElementById(`configurations-${id}`);
  if (document.body.createTextRange) {
    const range = document.body.createTextRange();
    range.moveToElementText(node);
    range.select();
  } else if (window.getSelection) {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(node);
    selection.removeAllRanges();
    selection.addRange(range);
  } else {
    alertify.notify("Selection not supported by your browser", "error", 5);
  }
  document.execCommand("copy");
}

Object.assign(action, {
  "Device properties": (d) => showTypePanel("device", d.id),
  "Link properties": (l) => showTypePanel("link", l.id),
  "Pool properties": (p) => showTypePanel("pool", p.id),
  Connect: (d) => showPanel("device_connection", d.id),
  Configuration: (d) => showDeviceConfiguration(d),
});
