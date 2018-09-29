/*
global
addObjectToTable: false
importTopology: false
devices: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Display the device connection modal.
 * @param {id} id - Device id.
 */
function connectionParametersModal(id) { // eslint-disable-line no-unused-vars
  $('#connection-parameters-form').trigger('reset');
  $('#connection-parameters').modal('show');
}

(function() {
  for (let i = 0; i < devices.length; i++) {
    addObjectToTable('create', 'device', devices[i]);
  }

  $('#user-credentials,#device-credentials').prop('disabled', true);
  $('#authentication').change(function () {
    $('#user-credentials,#device-credentials').prop('disabled', !$(this). prop("checked"));
  });
})();

document.getElementById('file').onchange = function() {
  importTopology('Device');
};
