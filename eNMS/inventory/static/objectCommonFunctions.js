/*
global
alertify: false
call: false
fCall: false
partial: false
*/

/**
 * Display the device automation modal.
 * @param {id} id - Device id.
 */
// eslint-disable-next-line
function deviceAutomationModal(id) {
  call(`/get/device/${id}`, function(device) {
    $("#device-automation-button").unbind("click");
    $("#device-automation-button").click(partial(saveDeviceJobs, id));
    $("#jobs").selectpicker("deselectAll");
    $("#jobs").selectpicker("val", device.jobs.map((d) => d.id));
    $("#device-automation").modal("show");
  });
}

/**
 * Update device jobs.
 * @param {id} id - Device id.
 */
function saveDeviceJobs(id) {
  const url = `/inventory/save_device_jobs/${id}`;
  fCall(url, "#device-automation-form", function(device) {
    alertify.notify("Changes saved.", "success", 5);
    $("#device-automation").modal("hide");
  });
}

/**
 * Start an SSH session to the device.
 * @param {id} id - Device id.
 */
function sshConnection(id) {
  const url = `/inventory/connection/${id}`;
  fCall(url, `#${id}-connection-parameters-form`, function(result) {
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
    $(`#${id}-connection-panel`).remove();
  });
}
