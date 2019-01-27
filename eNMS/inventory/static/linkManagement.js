/*
global
addInstance: false
doc: false
links: false
*/

$('#table thead tr').clone(true).appendTo('#table thead');
$('#table thead tr:eq(1) th').each(function(i) {
  var title = $(this).text();
  if (!['Edit', 'Duplicate', 'Delete'].includes(title)) {
    $(this).html('<input type="text" style="width: 100%;"/>');
    $('input', this).on('keyup change', function() {
      if (table.column(i).search() !== this.value) {
        table.column(i).search(this.value).draw();
      }
    });
  }
});

const table = $('#table').DataTable({
  sDom: '',
  orderCellsTop: true,
  fixedHeader: true
}); // eslint-disable-line

/**
 * Table Actions.
 * @param {values} values - values array.
 * @param {link} link - Link properties.
 */
function tableActions(values, link) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('link', '${link.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('link', '${link.id}', true)">
    Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="confirmDeletion('link', '${link.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  for (let i = 0; i < links.length; i++) {
    addInstance('create', 'link', links[i]);
  }
})();
