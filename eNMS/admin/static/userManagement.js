/*
global
addInstance: false
convertSelect: false
doc: false
users: false
*/

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  convertSelect('#user-permissions');
  perColumnSearch('user', 'user', ['Edit', 'Duplicate', 'Delete']);
})();
