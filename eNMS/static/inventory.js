/*
global
action: false
alertify: false
call: false
createPanel: false
diffview: false
fCall: false
getRuntimes: false
openUrl: false
showPanel: false
showTypePanel: false
table: false
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
function showConfiguration(id, name) {
  createPanel("display", `Configuration - Device ${name}`, id, () => {
    call(`/get/configuration/${id}`, (config) => {
      $(`#display-${id}`).html(`<pre>${config.result}</pre>`);
    });
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
      initSelect($(`#devices-${id}`), `pool_objects-${id}`, "device");
      pool.devices.forEach(o => $(`#devices-${id}`).append(new Option(o.name, o.id)));
      $(`#devices-${id}`).val(pool.devices.map((n) => n.id)).trigger("change");
    });
  });
}

// eslint-disable-next-line
function updatePools(pool) {
  alertify.notify("Update starting...", "success", 5);
  const endpoint = pool ? `/update_pool/${pool}` : "/update_all_pools";
  call(endpoint, function() {
    table.ajax.reload(null, false);
    alertify.notify("Update successful.", "success", 5);
  });
}

// eslint-disable-next-line
function showDeviceResultsPanel(id, name, type) {
  createPanel("device_results", `Results - ${name}`, id, function() {
    configureCallbacks(id, type);
    getRuntimes(id, type);
  });
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
  Connect: (d) => showPanel("connection", d.id),
  Configuration: (d) => showConfigurationPanel(d.id, d.name),
});
