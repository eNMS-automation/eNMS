/*
global
doc: false
initTable: false
*/

const toExclude = ['Edit', 'Duplicate', 'Delete']
let table = initTable('link', 'link', toExclude);

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
})();
