import { currentStore } from "../administration.js";
import { call, configureNamespace } from "../base.js";
import { tables } from "../table.js";

tables.vlan = class extends tables.data {};

function getNextVlanId(_, id) {
  call({
    url: "/filtering/vlan",
    data: { constraints: { store: [currentStore.name] }, bulk: "vlan_id" },
    callback: (vlanIds) => {
      $(`#vlan-vlan_id${id ? `-${id}` : ""}`).val(Math.max(...vlanIds) + 1);
    },
  });
}

tables.vlan.prototype.type = "vlan";

configureNamespace("datastore", [getNextVlanId]);
