import { currentStore } from "../administration.js";
import { tables } from "../table.js";

tables.store = class extends tables.data {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    row.scoped_name = `<a href="#" onclick="eNMS.administration.enterStore
        ({ id: ${row.id}})">
          <span class="glyphicon glyphicon-book" style="margin-left: 8px"></span>
          <b style="margin-left: 6px">${row.scoped_name}</b>
        </a>`;
    return row;
  }

  get filteringConstraints() {
    return currentStore ? {} : { store_filter: "empty" };
  }
};

tables.store.prototype.type = "store";
