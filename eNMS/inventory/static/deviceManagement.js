/*
global
convertSelect: false
doc: false
perColumnSearch: false
*/

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  convertSelect('#jobs');
  perColumnSearch('device', 'device', [
    'Edit',
    'Duplicate',
    'Delete',
    'Automation',
    'Connect',
  ]);
})();
