/*
global
doc: false
initTable: false
refreshTable: false
*/

const toExclude = [
  "Logs",
  "Progress",
  "Results",
  "Run",
  "Edit",
  "Duplicate",
  "Delete",
];
// eslint-disable-next-line no-unused-vars
let table = initTable("service", "service", toExclude);

(function() {
  doc("https://enms.readthedocs.io/en/latest/services/index.html");
  refreshTable(5000);
})();
