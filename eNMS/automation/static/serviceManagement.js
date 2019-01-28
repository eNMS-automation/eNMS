/*
global
doc: false
getStatus: false
initTable: false
*/

const toExclude = ['Logs', 'Run', 'Edit', 'Duplicate', 'Delete']
let table = initTable('service', 'service', toExclude);

(function() {
  doc('https://enms.readthedocs.io/en/latest/services/index.html');
  getStatus();
})();
