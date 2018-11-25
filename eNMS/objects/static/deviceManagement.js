/*
global
addInstance: false
convertSelect: false
devices: false
doc: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Table Actions.
 * @param {values} values - values array.
 * @param {device} device - Device properties.
 */
function tableActions(values, device) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="deviceAutomationModal('${device.id}')">Automation</button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="connectionParametersModal('${device.id}')">Connect</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('device', '${device.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('device', '${device.id}', true)">
    Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="confirmDeletion('device', '${device.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  convertSelect('#jobs');
  for (let i = 0; i < devices.length; i++) {
    addInstance('create', 'device', devices[i]);
  }
})();
