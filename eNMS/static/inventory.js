/*
global
action: false
alertify: false
call: false
createPanel: false
diffview: false
fCall: false
openUrl: false
showPanel: false
showTypePanel: false
table: false
*/

/**
 * Update device jobs.
 * @param {id} id - Device id.
 */
// eslint-disable-next-line
function saveDeviceJobs(id) {
  fCall(`/save_device_jobs/${id}`, `#${id}-device-automation-form`, function(
    device
  ) {
    alertify.notify("Changes saved.", "success", 5);
    $(`#automation-panel-${id}`).remove();
  });
}

/**
 * Start an SSH session to the device.
 * @param {id} id - Device id.
 */
// eslint-disable-next-line
function sshConnection(id) {
  fCall(`/connection-${id}`, `#connection-parameters-form-${id}`, function(
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

/**
 * Show Filtering Panel
 */
// eslint-disable-next-line
function showConfigurationPanel(id, name) {
  createPanel(`configuration`, `Configuration - Device ${name}`, id, function(
    panel
  ) {
    configureCallbacks(id);
    displayConfigurations(id);
  });
}

/**
 * Display configurations.
 * @param {int} id - Device ID.
 */
function displayConfigurations(id) {
  call(`/get_configurations-${id}`, (configurations) => {
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
    $(`#display-${id},#compare_with-${id}`).selectpicker("render");
    $(`#configurations-${id}`).text(configurations[$(`#display-${id}`).val()]);
  });
}

/**
 * Clear the configurations
 */
// eslint-disable-next-line
function clearConfigurations(id) {
  call(`/clear_configurations-${id}`, () => {
    $(`#configurations-${id},#compare_with-${id},#display-${id}`).empty();
    alertify.notify("Configurations cleared.", "success", 5);
    $(`#configuration-${id}`).remove();
  });
}

/**
 * Configure callbacks.
 */
// eslint-disable-next-line
function configureCallbacks(id) {
  $(`#display-${id}`).on("change", function() {
    call(`/get_configurations-${id}`, (configurations) => {
      $(`#configurations-${id}`).text(
        configurations[$(`#display-${id}`).val()]
      );
    });
  });

  $(`#compare_with-${id}`).on("change", function() {
    $(`#configurations-${id}`).empty();
    const v1 = $(`#display-${id}`).val();
    const v2 = $(`#compare_with-${id}`).val();
    call(`/get_diff-${id}-${v1}-${v2}`, function(data) {
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

/**
 * Update pool objects.
 */
// eslint-disable-next-line
function savePoolObjects(id) {
  fCall(`/save_pool_objects-${id}`, `#pool-objects-form-${id}`, function() {
    alertify.notify("Changes saved.", "success", 5);
    $(`#pool_objects-${id}`).remove();
  });
}

/**
 * Update one or all pools.
 * @param {pool} pool - Id of a pool or 'all'.
 */
// eslint-disable-next-line
function updatePool(pool) {
  alertify.notify("Update starting...", "success", 5);
  call(`/update_pool-${pool}`, function() {
    table.ajax.reload(null, false);
    alertify.notify("Update successful.", "success", 5);
  });
}

Object.assign(action, {
  "Device properties": (d) => showTypePanel("device", d.id),
  "Link properties": (l) => showTypePanel("link", l.id),
  "Pool properties": (p) => showTypePanel("pool", p.id),
  Connect: (d) => showPanel("connection", d.id),
  Configuration: (d) => showConfigurationPanel(d.id, d.name),
  Automation: (d) => showPanel("device_automation", d.id),
});
