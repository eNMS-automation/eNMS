/*
global
addInstance: false
doc: false
links: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

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
