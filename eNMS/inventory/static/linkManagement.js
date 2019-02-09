/*
global
convertSelect: false
doc: false
initTable: false
*/

let table = initTable( // eslint-disable-line no-unused-vars
  'link', 'link', ['Edit', 'Duplicate', 'Delete']
);

(function() {
  convertSelect('#link-source', '#link-destination');
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
})();
