/*
global
convertSelect: false
*/

let table = initTable('logrule', 'logrule', ['Edit', 'Delete']);

(function() {
  convertSelect('#logrule-jobs');
  refreshTable(15000);
})();
