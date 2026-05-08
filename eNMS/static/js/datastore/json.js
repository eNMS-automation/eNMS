/*
global
JSONEditor: false
*/

import { call, configureNamespace, downloadFile } from "../base.js";
import { tables } from "../table.js";

tables.json = class extends tables.data {
  rowButtons(row) {
    return super.rowButtons(row).toSpliced(
      1,
      0,
      `
      <li>
        <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.datastore.downloadJSONObject('${row.id}')"
          data-tooltip="Download JSON Object as File"
        >
          <span class="glyphicon glyphicon-download"></span>
        </button>
      </li>`
    );
  }
};

function downloadJSONObject(id) {
  call({
    url: `/get/json/${id}`,
    callback: (result) => {
      downloadFile(`json-object-${id}`, JSON.stringify(result.value, null, 2), "json");
    },
  });
}

tables.json.prototype.type = "json";

configureNamespace("datastore", [downloadJSONObject]);
