/*
global
addObjectToTable: false
doc: false
links: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  for (let i = 0; i < links.length; i++) {
    addObjectToTable('create', 'link', links[i]);
  }
})();
