/*
global
convertSelect: false
doc: false
initTable: false
*/

let table = initTable("device", "device", [
  "Edit",
  "Duplicate",
  "Delete",
  "Automation",
  "Connect",
], true);

(function() {
  doc("https://enms.readthedocs.io/en/latest/inventory/objects.html");
  $("#restrict-pool").on("change", function() {
    table.ajax.reload(null, false);
  });
  $("#restrict-pool").selectpicker("selectAll");
})();
