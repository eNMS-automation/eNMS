/*
global
alertify: false
*/

/**
 * Open new tab at the provided URL.
 * @param {url} url - URL.
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
      setTimeout(function () {
        if (result.redirection) {
          openUrl(`${protocol}//${hostname}/terminal${result.port}/`);
        } else {
          openUrl(`${protocol}//${hostname}:${result.port}`);
        }
      }, 500);
      const message = `Connection to ${result.device} on port ${result.port}.`;
      alertify.notify(message, 'success', 15);
    },
  });
}
