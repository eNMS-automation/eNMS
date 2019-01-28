/*
global
addInstance: false
convertSelect: false
devices: false
doc: false
*/

perColumnSearch([
  'Edit',
  'Duplicate',
  'Delete',
  'Automation',
  'Connect'
]);

const table = $('#table').DataTable({
  ordering: false,
  fixedHeader: true,
  processing: true,
  serverSide: true,
  ajax: '/server_side_processing/device/device',
}); // eslint-disable-line

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  convertSelect('#jobs');
})();
