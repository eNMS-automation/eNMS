/*
global
convertSelect: false
doc: false
initTable: false
*/

let table = initTable(
  'device', 'device', ['Edit', 'Duplicate', 'Delete', 'Automation', 'Connect']
);

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  convertSelect('#jobs');
})();
