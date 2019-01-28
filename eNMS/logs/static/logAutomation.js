/*
global
convertSelect: false
*/

let table = initTable('logrule', 'logrule', []);

(function() {
  convertSelect('#logrule-jobs');
  refreshTable(15000);
})();
