/*
global
addInstance: false
doc: false
links: false
*/

const toExclude = ['Edit', 'Duplicate', 'Delete', 'Source', 'Destination'];

$('#table thead tr').clone(true).appendTo('#table thead');
$('#table thead tr:eq(1) th').each(function(i) {
  var title = $(this).text();
  if (!toExclude.includes(title)) {
    $(this).html('<input type="text" style="width: 100%;"/>');
    $('input', this).on('keyup change', function() {
      if (table.column(i).search() !== this.value) {
        table.column(i).search(this.value).draw();
      }
    });
  }
});

const table = $('#table').DataTable({
  ordering: false,
  fixedHeader: true,
  processing: true,
  serverSide: true,
  ajax: '/server_side_processing/link',
}); // eslint-disable-line

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
})();
