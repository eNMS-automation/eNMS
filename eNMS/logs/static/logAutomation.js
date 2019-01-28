/*
global
convertSelect: false
initTable: false
refreshTable: false
*/

let table = initTable( // eslint-disable-line no-unused-vars
  'logrule', 'logrule', ['Edit', 'Delete']
);

(function() {
  convertSelect('#logrule-jobs');
  refreshTable(15000);
})();
