/*
global
convertSelect: false
doc: false
initTable: false
*/

const toExclude = ['Edit', 'Duplicate', 'Delete', 'Automation', 'Connect'];
let table = initTable('device', 'device', toExclude);

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  convertSelect('#jobs');
})();
