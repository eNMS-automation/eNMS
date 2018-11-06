/*
global
alertify: false
fCall: false
partial: false
*/

/**
 * Flip Combo box depending on whether or not authentication is selected.
 */
function flipAuthenticationCombo() {
  $('#user-credentials,#device-credentials').prop(
    'disabled', !$('#authentication').prop('checked')
  );
}

(function() {
  $('#authentication').change(function() {
    flipAuthenticationCombo();
  });
})();

/**
 * Open new tab at the provided URL.
 * @param {url} url - URL.
 */
function openUrl(url) {
  let win = window.open(url, '_blank');
  win.focus();
}

/**
 * Display the device connection modal.
 * @param {id} id - Device id.
 */
function connectionParametersModal(id) { // eslint-disable-line no-unused-vars
  $('#connection-button').unbind('click');
  $('#connection-button').click(partial(sshConnection, id));
  $('#connection-parameters-form').trigger('reset');
  flipAuthenticationCombo();
  $('#edit-device').modal('hide');
  $('#connection-parameters').modal('show');
}

/**
 * Start an SSH session to the device.
 * @param {id} id - Device id.
 */
function sshConnection(id) { // eslint-disable-line no-unused-vars
  const url = `/objects/connection/${id}`;
  fCall(url, '#connection-parameters-form', function(result) {
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
    alertify.notify(link, 'success', 15);
    const warning = `Don't forget to turn off the pop-up blocker !`;
    alertify.notify(warning, 'error', 20);
    $('#connection-parameters').modal('hide');
  });
}
