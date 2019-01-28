/*
global
convertSelect: false
doc: false
perColumnSearch: false
*/

perColumnSearch([
  'Edit',
  'Duplicate',
  'Delete',
  'Automation',
  'Connect',
]);

const table = $('#table').DataTable({ // eslint-disable-line
  ordering: false,
  fixedHeader: true,
  processing: true,
  serverSide: true,
  ajax: '/server_side_processing/device/device',
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  convertSelect('#jobs');
})();
