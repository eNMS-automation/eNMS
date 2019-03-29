import {
  convertSelect,
  doc,
  initTable,
} from "../../static/enms/base.js";

window.table = initTable("user", "user", ["Edit", "Duplicate", "Delete"]);

(function() {
  doc("https://enms.readthedocs.io/en/latest/security/access.html");
  convertSelect("#user-permissions", "#user-pools");
})();
