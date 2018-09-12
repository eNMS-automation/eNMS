/*
global
alertify: false
*/

function openUrl(url) {
  let win = window.open(url, '_blank');
  win.focus();
}

/**
 * Start an SSH session to the device.
 */
function SshConnection() { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/views/connection/${$(`#device-name`).val()}`,
    success: function(result) {
      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      openUrl(`${protocol}//${hostname}:${result.port}`);
      const message = `Connection to ${result.device} on port ${result.port}.`;
      alertify.notify(message, 'success', 15);
    },
  });
}
