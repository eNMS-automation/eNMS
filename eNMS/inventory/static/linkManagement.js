/*
global
doc: false
perColumnSearch: false
*/

perColumnSearch([
  'Edit',
  'Duplicate',
  'Delete',
  'Source',
  'Destination',
]);

const table = $('#table').DataTable({ // eslint-disable-line
  ordering: false,
  fixedHeader: true,
  processing: true,
  serverSide: true,
  ajax: '/server_side_processing/link/link',
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
})();
