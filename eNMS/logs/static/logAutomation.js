/*
global
convertSelect: false
initTable: false
refreshTable: false
*/

// eslint-disable-next-line no-unused-vars
let table = initTable("logrule", "logrule", ["Edit", "Delete"]);

(function() {
  convertSelect("#logrule-jobs");
  refreshTable(15000);
})();
