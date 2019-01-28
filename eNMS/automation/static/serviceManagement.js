/*
global
addInstance: false
doc: false
getStatus: false
*/

/*
let pageScrollPos;
const table = $('#table').DataTable({ // eslint-disable-line
  'preDrawCallback': function(settings) {
    pageScrollPos = $(window).scrollTop();
  },
  'drawCallback': function(settings) {
    $(window).scrollTop(pageScrollPos);
  },
});
*/

(function() {
  doc('https://enms.readthedocs.io/en/latest/services/index.html');
  table = perColumnSearch('service', 'service', [
    'Logs',
    'Run',
    'Edit',
    'Duplicate',
    'Delete'
  ]);
  getStatus('service');
})();
