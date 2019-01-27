/*
global
addInstance: false
convertSelect: false
devices: false
doc: false
*/

const table = $('#table').DataTable({
  'processing': true,
  'serverSide': true,
  'ajax': '/server_side_processing'
}); // eslint-disable-line

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  convertSelect('#jobs');
})();
