/*
global
addObjectToTable: false
devices: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

(function() {
  $('#doc-link').attr(
    'href',
    'https://enms.readthedocs.io/en/latest/inventory/objects.html'
  );
  for (let i = 0; i < devices.length; i++) {
    addObjectToTable('create', 'device', devices[i]);
  }
})();
