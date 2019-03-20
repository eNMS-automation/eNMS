/*
global
doc: false
initTable: false
refreshTable: false
*/

const toExclude = ['Progress', 'Logs', 'Run', 'Edit', 'Duplicate', 'Delete'];
let table = initTable( // eslint-disable-line no-unused-vars
  'service', 'service', toExclude
);

(function() {
  doc('https://enms.readthedocs.io/en/latest/services/index.html');
  refreshTable(5000);
})();
