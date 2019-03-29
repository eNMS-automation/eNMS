/*
global
convertSelect: false
doc: false
initTable: false
*/

let table = initTable("link", "link", ["Edit", "Duplicate", "Delete"]);

(function() {
  doc("https://enms.readthedocs.io/en/latest/inventory/objects.html");
  $("#restrict-pool").on("change", function() {
    table.ajax.reload(null, false);
  });
  convertSelect("#link-source", "#link-destination", "#restrict-pool");
  $("#restrict-pool").selectpicker("selectAll");
})();
