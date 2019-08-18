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
function showConfigurationPanel(id, name) {
  createPanel(
    `configuration`,
    `Configuration - Device ${name}`,
    id,
    function() {
      configureCallbacks(id);
      displayConfigurations(id);
    }
  );
}

function displayConfigurations(id) {
  call(`/get_configurations/${id}`, (configurations) => {
    $(`#display-${id},#compare_with-${id}`).empty();
    const times = Object.keys(configurations);
    times.forEach((option) => {
      $(`#display-${id},#compare_with-${id}`).append(
        $("<option></option>")
          .attr("value", option)
          .text(option)
      );
    });
    $(`#display-${id},#compare_with-${id}`).val(times[times.length - 1]);
    $(`#display-${id},#compare_with-${id}`).selectpicker("refresh");
    $(`#configurations-${id}`).text(configurations[$(`#display-${id}`).val()]);
  });
}

// eslint-disable-next-line
function clearConfigurations(id) {
  call(`/clear_configurations/${id}`, () => {
    $(`#configurations-${id},#compare_with-${id},#display-${id}`).empty();
    alertify.notify("Configurations cleared.", "success", 5);
    $(`#configuration-${id}`).remove();
  });
}

// eslint-disable-next-line
function configureCallbacks(id) {
  $(`#display-${id}`).on("change", function() {
    call(`/get_configurations/${id}`, (configurations) => {
      $(`#configurations-${id}`).text(
        configurations[$(`#display-${id}`).val()]
      );
    });
  });

  $(`#compare_with-${id}`).on("change", function() {
    $(`#configurations-${id}`).empty();
    const v1 = $(`#display-${id}`).val();
    const v2 = $(`#compare_with-${id}`).val();
    call(`/get_configuration_diff/${id}/${v1}/${v2}`, function(data) {
      $(`#configurations-${id}`).append(
        diffview.buildView({
          baseTextLines: data.first,
          newTextLines: data.second,
          opcodes: data.opcodes,
          baseTextName: `${v1}`,
          newTextName: `${v2}`,
          contextSize: null,
          viewType: 0,
        })
      );
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
      $(`#devices-${id}`).selectpicker("val", pool.devices.map((n) => n.id));
      $(`#links-${id}`).selectpicker("val", pool.links.map((l) => l.id));
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
