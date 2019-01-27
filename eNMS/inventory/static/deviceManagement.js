/*
global
addInstance: false
convertSelect: false
devices: false
doc: false
*/

$('#table tfoot th').each(function() {
  var title = $(this).text();
  $(this).html('<input type="text" placeholder="Search '+title+'" />');
});

const table = $('#table').DataTable({
  'processing': true,
  'serverSide': true,
  'ajax': '/server_side_processing'
}); // eslint-disable-line

    // Apply the search
    table.columns().every( function () {
        var that = this;
 
        $( 'input', this.footer() ).on( 'keyup change', function () {
            if ( that.search() !== this.value ) {
                that
                    .search( this.value )
                    .draw();
            }
        } );
    } );

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  convertSelect('#jobs');
})();
