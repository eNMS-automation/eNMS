/*
global
alertify: false
*/

/**
 * Start an SSH session to the device.
 */
function SshConnection() { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/views/connection/${$(`#device-name`).val()}`,
    success: function(result) {
      const message = `Connection to ${result.device} on port ${result.port}.`;
      alertify.notify(message, 'success', 15);
    },
  });
}
