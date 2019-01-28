/*
global
doc: false
getStatus: false
*/

(function() {
  doc('https://enms.readthedocs.io/en/latest/services/index.html');
  table = initTable('service', 'service', [
    'Logs',
    'Run',
    'Edit',
    'Duplicate',
    'Delete'
  ]);
  getStatus();
})();
