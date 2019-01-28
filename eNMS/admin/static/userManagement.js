/*
global
addInstance: false
convertSelect: false
doc: false
users: false
*/

const table = $('#table').DataTable({ // eslint-disable-line
  ordering: false,
  fixedHeader: true,
  processing: true,
  serverSide: true,
  ajax: '/server_side_processing/user/user',
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  convertSelect('#user-permissions');
})();
