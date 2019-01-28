/*
global
addInstance: false
doc: false
links: false
*/

perColumnSearch([
  'Edit',
  'Duplicate',
  'Delete',
  'Source',
  'Destination'
]);

const table = $('#table').DataTable({
  ordering: false,
  fixedHeader: true,
  processing: true,
  serverSide: true,
  ajax: '/server_side_processing/link/link',
}); // eslint-disable-line

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
})();
