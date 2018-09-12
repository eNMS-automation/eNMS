/*
global
alertify: false
*/

/**
 * Start an SSH session to the device.
 */
function connectToDevice() { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/views/connect_to_${$(`#device-name`).val()}`,
    success: function(result) {
      message = `Connection to ${result.device} on port ${result.port}.`;
      alertify.notify(message, 'success', 15);
    },
  });
}
