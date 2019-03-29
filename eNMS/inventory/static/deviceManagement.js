/*
global
convertSelect: false
doc: false
initTable: false
*/

let table = initTable(
  // eslint-disable-line no-unused-vars
  "device",
  "device",
  ["Edit", "Duplicate", "Delete", "Automation", "Connect"]
);

(function() {
  doc("https://enms.readthedocs.io/en/latest/inventory/objects.html");
  $("#restrict-pool").on("change", function() {
    table.ajax.reload(null, false);
  });
  convertSelect("#jobs", "#restrict-pool");
  $("#restrict-pool").selectpicker("selectAll");
})();
