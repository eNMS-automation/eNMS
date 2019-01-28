/*
global
addInstance: false
convertSelect: false
doc: false
users: false
*/

perColumnSearch('user', 'user', ['Edit', 'Duplicate', 'Delete']);

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  convertSelect('#user-permissions');
})();
