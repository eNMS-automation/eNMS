/*
global
convertSelect: false
doc: false
initTable: false
*/

// eslint-disable-next-line no-unused-vars
let table = initTable("user", "user", ["Edit", "Duplicate", "Delete"]);

(function() {
  doc("https://enms.readthedocs.io/en/latest/security/access.html");
  convertSelect("#user-permissions", "#user-pools");
})();
