/*
global
addObjectToTable: false
devices: false
importTopology: false
partial: false
sshConnection: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

(function() {
  for (let i = 0; i < devices.length; i++) {
    addObjectToTable('create', 'device', devices[i]);
  }
})();

document.getElementById('file').onchange = function() {
  importTopology('Device');
};
