/*
global
addObjectToTable: false
devices: false
fields: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

(function() {
  for (let i = 0; i < devices.length; i++) {
    addObjectToTable('create', 'device', devices[i]);
  }
})();

document.getElementById('file').onchange = function() {
  $('#form').submit();
};
