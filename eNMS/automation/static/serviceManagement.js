/*
global
addInstance: false
doc: false
getStatus: false
services: false
*/

let pageScrollPos;
const table = $('#table').DataTable({ // eslint-disable-line
  'preDrawCallback': function(settings) {
    pageScrollPos = $(window).scrollTop();
  },
  'drawCallback': function(settings) {
    $(window).scrollTop(pageScrollPos);
  },
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/services/index.html');
  for (let i = 0; i < services.length; i++) {
    addInstance('create', 'service', services[i]);
  }
  getStatus('service');
})();
