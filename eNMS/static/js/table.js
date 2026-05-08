/*
global
applicationPath: false
filePath: false
settings: false
tableProperties: false
*/

import {
  call,
  configureNamespace,
  copyToClipboard,
  createTooltip,
  createTooltips,
  downloadFile,
  loadTypes,
  notify,
  openPanel,
  sanitize,
  serializeForm,
  showChangelogPanel,
  showConfirmationPanel,
  userIsActive,
} from "./base.js";
import {
  currentStore,
  displayFolderPath,
  displayStorePath,
  folderPath,
} from "./administration.js";
import { updateNetworkRightClickBindings } from "./networkBuilder.js";

export let tables = {};
export let tableInstances = {};
export const models = {};
let waitForSearch = false;
let debounceTimer;

$.fn.dataTable.ext.errMode = "none";

export class Table {
  constructor(id, constraints, relation) {
    let self = this;
    this.relation = relation;
    if (relation) this.relationString = JSON.stringify(relation).replace(/"/g, "'");
    this.columns = tableProperties[this.type];
    this.constraints = constraints;
    let visibleColumns = localStorage.getItem(`${this.type}_table`);
    if (visibleColumns) visibleColumns = visibleColumns.split(",");
    this.columns.forEach((column) => {
      if (visibleColumns) column.visible = visibleColumns.includes(column.data);
      column.name = column.data;
      if (!column.html) column.render = $.fn.dataTable.render.text();
    });
    this.userFiltering = localStorage.getItem(`userFiltering-${this.type}`) || "users";
    this.id = `${this.type}${id ? `-${id}` : ""}`;
    this.model = this.modelFiltering || this.type;
    this.displayPagination = false;
    tableInstances[this.id] = this;
    // eslint-disable-next-line new-cap
    this.table = $(`#table-${this.id}`).DataTable({
      serverSide: true,
      orderCellsTop: true,
      autoWidth: false,
      scrollX: true,
      order: this.tableOrdering,
      pagingType: "simple",
      drawCallback: function() {
        $(".paginate_button > a").on("focus", function() {
          $(this).blur();
        });
        if (!self.displayPagination) self.setPagination();
        createTooltips();
      },
      sDom: "tilp",
      columns: this.columns,
      columnDefs: [{ className: "dt-center", targets: "_all" }],
      initComplete: function() {
        this.api()
          .columns()
          .every(function(index) {
            const data = self.columns[index];
            let element;
            const elementId = `${self.type}_filtering-${data.data}`;
            if (data.search == "text") {
              element = `
              <div class="input-group table-search" style="width:100%">
                <input
                  id="${elementId}"
                  name="${data.data}"
                  type="text"
                  placeholder="&#xF002;"
                  class="form-control search-input-${self.id}"
                  style="font-family:Arial, FontAwesome;
                  height: 30px; margin-top: 5px"
                >
                <span class="input-group-btn" style="width: 10px">
                  <button
                    id="${elementId}-search"
                    class="btn btn-default pull-right"
                    type="button"
                    style="height: 30px; margin-top: 5px">
                      <span
                        class="glyphicon glyphicon-center glyphicon-menu-down"
                        aria-hidden="true"
                        style="font-size: 10px">
                      </span>
                  </button>
                </span>
              </div>`;
            } else if (data.search == "bool") {
              element = `
                <div class="input-group table-search" style="width:100%">
                  <select
                    id="${elementId}"
                    name="${data.data}"
                    class="form-control search-list-${self.id}"
                    style="width: 100%; height: 30px; margin-top: 5px"
                  >
                    <option value="">Any</option>
                    <option value="bool-true">
                      ${data?.search_labels?.true || "True"}
                    </option>
                    <option value="bool-false">
                      ${data?.search_labels?.false || "False"}
                    </option>
                  </select>
                </div>`;
            }
            const eventType = data.search == "text" ? "keyup" : "change";
            const sendAlert = settings.tables.search.notification;
            $(element)
            .appendTo($(this.header()))
            .on(eventType, function () {
              if (waitForSearch) return;
              clearTimeout(debounceTimer);
              debounceTimer = setTimeout(function () {
                waitForSearch = true;
                if (sendAlert) notify("Searching...", "success", 5, true);
                self.table.page(0).ajax.reload(function () {
                  if (sendAlert) notify("Search completed successfully", "success", 5, true);
                  waitForSearch = false;
                }, false);
              }, settings.tables.search.timer);
              })
              .on("keydown", function(e) {
                if (e.key === "Enter") e.preventDefault();
              })
              .on("click", function(e) {
                e.stopPropagation();
              });
          });
        $(`#controls-${self.id}`).append(self.controls);
        self.postProcessing();
      },
      ajax: {
        url: `/filtering/${this.model}`,
        type: "POST",
        contentType: "application/json",
        data: (data) => {
          this.data = Object.keys(tableSearch).length
            ?  tableSearch
            : { ...this.getFilteringData(), ...self.filteringData };
          Object.assign(data, {
            export: self.csvExport,
            clipboard: self.copyClipboard,
            pagination: self.displayPagination,
            ...this.data,
          });
          self.copyClipboard = false;
          return JSON.stringify(data);
        },
        dataSrc: function(result) {
          if (result.error) {
            notify(result.error, "error", 5);
            return [];
          }
          if (self.csvExport) {
            self.exportTable(result.full_result);
            self.csvExport = false;
          }
          if (result.clipboard) {
            copyToClipboard({ text: result.clipboard, includeText: false });
          }
          return result.data.map((instance) =>
            self.addRow({ properties: instance, tableId: self.id })
          );
        },
      },
    });
    $(window).resize(this.table.columns.adjust);
    $(`[name=table-${this.id}_length]`).selectpicker("refresh");
    const refreshRate = settings.tables.refresh[this.type];
    if (refreshRate) refreshTablePeriodically(this.id, refreshRate, true);
  }

  get tableOrdering() {
    return [0, "asc"];
  }

  exportTable(result) {
    const visibleColumns = this.columns
      .filter((column) => {
        const isExportable = typeof column.export === "undefined" || column.export;
        const visibleColumn = this.table.column(`${column.name}:name`).visible();
        return isExportable && visibleColumn;
      })
      .map((column) => column.name);
    result = result.map((instance) => {
      Object.keys(instance).forEach((key) => {
        if (!visibleColumns.includes(key)) delete instance[key];
      });
      return visibleColumns.map((column) => `"${instance[column]}"`);
    });
    downloadFile(
      this.type,
      [visibleColumns, ...result].map((e) => e.join(",")).join("\n"),
      "csv"
    );
  }

  getFilteringData() {
    let data = {};
    let bulkFiltering = $(`#${this.model}_filtering-form-${this.id}`).length;
    const serializedForm = bulkFiltering
      ? `#${this.model}_filtering-form-${this.id}`
      : `#search-form-${this.id}`;
    let form = serializeForm(serializedForm, `${this.model}_filtering`, bulkFiltering);
    for (const [key, value] of Object.entries(form)) {
      if (key.includes("_invert")) form[key] = ["y", "on", "bool-true"].includes(value);
    }
    Object.assign(data, {
      form: form,
      constraints: { ...this.constraints, ...this.filteringConstraints },
      columns: this.columns,
      type: this.type,
      rbac: this.defaultRbac || "read",
    });
    return data;
  }

  postProcessing() {
    let self = this;
    this.createfilteringTooltips();
    createTooltips();
    const visibleColumns = localStorage.getItem(`${this.type}_table`);
    this.columns.forEach((column) => {
      const visible = visibleColumns
        ? visibleColumns.split(",").includes(column.name)
        : "visible" in column
        ? column.visible
        : true;
      const columnTitle = column.data == "buttons" ? "Buttons" : column.title;
      $(`#column-display-${this.id}`).append(
        new Option(columnTitle || column.data, column.data, visible, visible)
      );
    });
    $(`#column-display-${this.id}`).selectpicker("refresh");
    $(`#column-display-${this.id}`).on("change", function() {
      self.columns.forEach((col) => {
        const isVisible =
          $(this).val() &&
          $(this)
            .val()
            .includes(col.data);
        self.table.column(`${col.name}:name`).visible(isVisible);
      });
      self.table.ajax.reload(null, false);
      self.createfilteringTooltips();
      localStorage.setItem(`${self.type}_table`, $(this).val());
    });
    self.table.columns.adjust();
  }

  setPagination() {
    const button = `
      <ul class="pagination" style="margin: 0px;">
        <li>
          <a
            onclick="eNMS.table.togglePaginationDisplay('${this.id}')"
            data-tooltip="Load Table Count"
            style="cursor: pointer;"
            >Load Table Count</a>
        </li>
      </ul>`;
    $(`#table-${this.id}_wrapper > .dataTables_info`)
      .html(button)
      .show();
  }

  createfilteringTooltip(property) {
    const elementId = `${this.type}_filtering-${property}`;
    createTooltip({
      persistent: true,
      name: elementId,
      target: `#${elementId}-search`,
      container: `#tooltip-overlay`,
      position: {
        my: "center-top",
        at: "center-bottom",
      },
      content: `
      <div class="modal-body">
        <label class="control-label col-md-3 col-sm-3 col-xs-12">
          Filter
        </label>
        <div class="col-md-9 col-sm-9 col-xs-12">
          <select
            id="${property}_filter"
            name="${property}_filter"
            class="form-control search-select-${this.id}"
            style="width: 100%; height: 30px"
          >
            <option value="inclusion">Inclusion</option>
            <option value="equality">Equality</option>
            <option value="regex">Regular Expression</option>
            <option value="empty">Empty</option>
          </select>
        </div>
        <br /><br />
        <label class="control-label col-md-3 col-sm-3 col-xs-12">
          Invert
        </label>
        <div class="col-md-9 col-sm-9 col-xs-12">
          <center>
            <input
              class="collapsed form-control-bool add-id"
              id="${property}_invert"
              name="${property}_invert"
              type="checkbox" 
              value="y"
            >
          </center>
        </div>
        <br />
      </div>`,
    });
  }

  createfilteringTooltips() {
    this.columns.forEach((column) => {
      if (column.search != "text") return;
      this.createfilteringTooltip(column.data);
    });
  }

  columnDisplay({ search = false } = {}) {
    const searchBox = search ? 'data-live-search="true"' : "";
    return `
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 200px;"
        type="button"
      >
        <select multiple
          id="column-display-${this.id}"
          title="Columns"
          class="form-control"
          ${searchBox}
          data-size="20"
          data-actions-box="true"
          data-selected-text-format="static"
        ></select>
      </button>`;
  }

  bulkFilteringButton() {
    const showPanelFunction =
      this.model == "service"
        ? `automation.openServicePanel('${this.id}', 'bulk-filter')`
        : `base.showInstancePanel('${this.model}', null, 'bulk-filter', '${this.id}')`;
    return `
      <button
        class="btn btn-info"
        onclick="eNMS.${showPanelFunction}"
        data-tooltip="Bulk Filtering"
        type="button"
      >
        <span class="glyphicon glyphicon-filter"></span>
      </button>`;
  }

  changelogButton(row) {
    return `
      <li>
        <button type="button" class="btn btn-sm btn-info"
        onclick="eNMS.table.displayRelationTable(
          'changelog', ${row.instance},
          {parent: '${this.type}', from: '${this.type}', to: 'logs'})"
          data-tooltip="Changelog"
          ><span class="glyphicon glyphicon-wrench"></span
        ></button>
      </li>`;
  }

  createNewButton() {
    if (this.relation && this.addRelationDisabled) return "";
    const onClick = this.relation
      ? `eNMS.base.showAddInstancePanel(
          '${this.id}', '${this.type}', ${this.relationString}
        )`
      : this.type == "service"
      ? `eNMS.automation.openServicePanel()`
      : this.type == "device" || this.type == "link"
      ? `eNMS.inventory.openObjectPanel('${this.type}')`
      : `eNMS.base.showInstancePanel('${this.type}')`;
    return `
      <button
        class="btn btn-primary"
        onclick="${onClick}"
        data-tooltip="${this.relation ? "Add" : "New"}"
        type="button"
      >
        <span class="glyphicon glyphicon-plus"></span>
      </button>`;
  }

  exportTableButton() {
    return `
      <button
        class="btn btn-primary"
        onclick="eNMS.table.exportTable('${this.id}')"
        data-tooltip="Export as .CSV"
        type="button"
      >
        <span class="glyphicon glyphicon-upload"></span>
      </button>`;
  }

  clearSearchButton() {
    return `
      <button
        class="btn btn-info"
        onclick="eNMS.table.clearSearch('${this.id}', true)"
        data-tooltip="Clear Search"
        type="button"
      >
      <span class="glyphicon glyphicon-remove"></span>
    </button>`;
  }

  refreshTableButton() {
    return `
      <button
        class="btn btn-info"
        onclick="eNMS.table.refreshTable('${this.id}', true)"
        data-tooltip="Refresh"
        type="button"
      >
        <span class="glyphicon glyphicon-refresh"></span>
      </button>`;
  }

  displayChangelogButton(type) {
    const typeVariable = type === undefined ? undefined : `'${type}'`;
    return `
      <button
        class="btn btn-info"
        onclick="eNMS.table.showTableChangelogPanel('${this.id}', ${typeVariable})"
        data-tooltip="Changelog"
        type="button"
      >
        <span class="glyphicon glyphicon-wrench"></span>
      </button>`;
  }

  copySearchLinkButton() {
    return `
      <button
        class="btn btn-info"
        onclick="eNMS.table.copySearchLinkToClipboard('${this.id}')"
        data-tooltip="Copy to Clipboard Hyperlink to Current Search"
        type="button"
      >
        <span class="glyphicon glyphicon-link"></span>
      </button>`;
  }

  copyTableButton() {
    return `
      <button
        class="btn btn-info"
        onclick="eNMS.table.copySelectionToClipboard('${this.id}')"
        data-tooltip="Copy Selection to Clipboard"
        type="button"
      >
      <span class="glyphicon glyphicon-pencil"></span>
    </button>`;
  }

  bulkEditButton() {
    const showPanelFunction =
      this.model == "service"
        ? `automation.openServicePanel('${this.id}', 'bulk-edit')`
        : `base.showInstancePanel('${this.model}', null, 'bulk-edit', '${this.id}')`;
    return `
      <button
        class="btn btn-primary"
        onclick="eNMS.${showPanelFunction}"
        data-tooltip="Bulk Edit"
        type="button"
      >
        <span class="glyphicon glyphicon-edit"></span>
      </button>`;
  }

  bulkDeletionButton() {
    const onClick = this.relation
      ? `eNMS.table.bulkRemoval('${this.id}', '${this.model}', ${this.relationString})`
      : `eNMS.table.showBulkDeletionPanel('${this.id}', '${this.model}')`;
    return `
      <button
        class="btn btn-danger"
        onclick="${onClick}"
        data-tooltip="Bulk Deletion"
        type="button"
      >
        <span class="glyphicon glyphicon-${this.relation ? "remove" : "trash"}"></span>
      </button>`;
  }

  deleteInstanceButton(row) {
    const onClick = this.relation
      ? `eNMS.base.removeInstance(
          '${this.id}', ${row.instance}, ${this.relationString}
        )`
      : `eNMS.base.showDeletionPanel(${row.instance}, '${this.id}')`;
    return `
      <li>
        <button type="button" class="btn btn-sm btn-danger"
        onclick="${onClick}" data-tooltip="Delete"><span class="glyphicon
        glyphicon-${this.relation ? "remove" : "trash"}"></span></button>
      </li>`;
  }

  userFilteringButton() {
    return `
      <button
        class="btn btn-info"
        onclick="eNMS.table.userFilteringDisplay('${this.id}')"
        data-tooltip="Personal or All ${this.type}s"
        type="button"
      >
        <span
          id="user-filtering-icon-${this.id}"
          class="fa fa-${this.userFiltering}">
        </span>
      </button>`;
  }

  serializedSearchField() {
    return `
      <div
        id="serialized-search-div"
        class="input-group table-search"
        style="width: 100%; padding: 3px 15px 3px 15px; display: none;"
      >
        <input
          id="serialized-search"
          name="serialized"
          type="text"
          placeholder="&#xF002; Search across all properties"
          class="form-control"
          style="font-family:Arial, FontAwesome;
          height: 30px; margin-top: 5px"
        >
      </div>`;
  }

  get userDisplayConstraints() {
    return this.userFiltering == "user"
      ? { creator: user.name, creator_filter: "equality" }
      : {};
  }

  addRow({ properties, tableId, derivedProperties }) {
    let row = { tableId: tableId, ...properties };
    row.instanceProperties = { id: row.id, name: row.name, type: row.type };
    if (derivedProperties) {
      derivedProperties.forEach((property) => {
        row.instanceProperties[property] = row[property];
      });
    }
    row.instance = JSON.stringify(row.instanceProperties).replace(/"/g, "'");
    if (this.buttons) row.buttons = this.buttons(row);
    return row;
  }
}

tables.device = class DeviceTable extends Table {
  addRow(kwargs) {
    let row = super.addRow({
      derivedProperties: ["last_runtime"],
      ...kwargs,
    });
    for (const model of ["service", "task", "pool"]) {
      const from = model == "service" ? "target_devices" : "devices";
      const to = model == "service" ? `target_${model}s` : `${model}s`;
      row[`${model}s`] = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
        '${model}', ${row.instance}, {parent: '${this.id}', from: '${from}',
        to: '${to}'})">${model.charAt(0).toUpperCase() + model.slice(1)}s</a></b>`;
    }
    return row;
  }

  get controls() {
    return [
      this.columnDisplay({ search: true }),
      this.displayChangelogButton(),
      this.refreshTableButton(),
      `
      <button
        class="btn btn-info"
        id="device-serialized-search-btn"
        onclick="eNMS.table.serializedSearch('device')"
        data-tooltip="Search across all properties"
        type="button"
      >
        <span class="glyphicon glyphicon-search"></span>
      </button>`,
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.copyTableButton(),
      this.createNewButton(),
      `
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 200px;"
        type="button"
      >
        <select id="device-type-dd-list" class="form-control"></select>
      </button>`,
      this.bulkEditButton(),
      this.exportTableButton(),
      ` <button
        type="button"
        class="btn btn-success"
        onclick="eNMS.automation.showRunServicePanel(
          {tableId: '${this.id}', type: '${this.type}'}
        )"
        data-tooltip="Run service on all devices in table"
      >
        <span class="glyphicon glyphicon-play"></span>
      </button>`,
      this.bulkDeletionButton(),
      this.serializedSearchField(),
    ];
  }

  buttons(row) {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 310px">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.inventory.showDeviceData(${row.instance})"
          data-tooltip="Network Data"
            ><span class="glyphicon glyphicon-cog"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.inventory.showDeviceResultsPanel(${row.instance})"
          data-tooltip="Results"
            ><span class="glyphicon glyphicon-list-alt"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-dark"
          onclick="eNMS.inventory.showConnectionPanel(${row.instance})"
          data-tooltip="Connection"
            ><span class="glyphicon glyphicon-console"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.type}', '${
      row.id
    }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.type}', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.automation.showRunServicePanel({instance: ${row.instance}})"
          data-tooltip="Run Service"><span class="glyphicon glyphicon-play">
          </span></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`;
  }

  postProcessing(...args) {
    let self = this;
    super.postProcessing(...args);
    let timer = false;
    document.getElementById("serialized-search").addEventListener("keyup", function() {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        self.table.page(0).ajax.reload(null, false);
      }, 500);
    });
    loadTypes("device");
  }
};

tables.network = class NetworkTable extends Table {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    const rowName = sanitize(row.name);
    row.name = `<b><a href="/network_builder/${row.path}">${rowName}</a></b>`;
    row.links = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'link', ${row.instance}, {parent: '${this.id}', from: 'networks',
      to: 'links'})">Links</a></b>`;
    row.devices = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'device', ${row.instance}, {parent: '${this.id}', from: 'networks',
      to: 'devices'})">Devices</a></b>`;
    return row;
  }

  postProcessing(...args) {
    let self = this;
    super.postProcessing(...args);
    updateNetworkRightClickBindings();
    $("#parent-filtering")
      .selectpicker()
      .on("change", function() {
        self.table.page(0).ajax.reload(null, false);
      });
  }

  get controls() {
    return [
      this.columnDisplay(),
      `
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 240px;"
        type="button"
      >
        <select
          id="parent-filtering"
          name="parent-filtering"
          class="form-control"
        >
          <option value="true">Display top-level networks</option>
          <option value="false">Display all networks</option>
        </select>
      </button>`,
      this.displayChangelogButton(),
      this.refreshTableButton(),
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.copyTableButton(),
      this.createNewButton(),
      this.bulkEditButton(),
      this.bulkDeletionButton(),
    ];
  }

  buttons(row) {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 150px">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.type}', '${
      row.id
    }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.type}', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`;
  }

  get filteringConstraints() {
    const parentFiltering = ($("#parent-filtering").val() || "true") == "true";
    return { networks_filter: parentFiltering ? "empty" : "union", type: "network" };
  }
};

tables.configuration = class ConfigurationTable extends Table {
  addRow(kwargs) {
    let row = super.addRow({
      derivedProperties: ["last_runtime"],
      ...kwargs,
    });
    const failureBtn = `<button type="button" class="btn btn-sm btn-danger">`;
    const successBtn = `<button type="button" class="btn btn-sm btn-success">`;
    for (const [key, value] of Object.entries(row)) {
      if (typeof value !== "string") continue;
      if (value.toLowerCase() == "failure") row[key] = `${failureBtn}Failure</button>`;
      if (value.toLowerCase() == "success") row[key] = `${successBtn}Success</button>`;
    }
    row.v1 = `<input type="radio" name="v1" value="${row.id}">`;
    row.v2 = `<input type="radio" name="v2" value="${row.id}">`;
    return row;
  }

  get defaultRbac() {
    return "configuration";
  }

  get modelFiltering() {
    return "device";
  }

  postProcessing(...args) {
    super.postProcessing(...args);
    $("#configuration-property-diff").selectpicker("refresh");
    $("#slider")
      .bootstrapSlider({
        value: 0,
        ticks: [...Array(6).keys()],
        formatter: (value) => `Lines of context: ${value}`,
        tooltip: "always",
      })
      .on("change", function() {
        refreshTable("configuration");
      });
  }

  get controls() {
    return [
      this.columnDisplay({ search: true }),
      `<input
        name="context-lines"
        id="slider"
        class="slider"
        style="width: 200px"
      >`,
      this.refreshTableButton(),
      this.bulkFilteringButton("device"),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.copyTableButton(),
      ` <button
        class="btn btn-info"
        onclick="eNMS.base.displayDiff('configuration', 'none')"
        data-tooltip="Compare"
        type="button"
      >
        <span class="glyphicon glyphicon-adjust"></span>
      </button>
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 200px;"
        type="button"
      >
        <select
          id="configuration-property-diff"
          class="form-control"
        >
          ${Object.entries(configurationProperties).map(
            ([value, name]) => `<option value="${value}">${name}</option>`
          )}
        </select>
      </button>`,
      this.bulkEditButton(),
      this.exportTableButton(),
      this.bulkDeletionButton(),
    ];
  }

  buttons(row) {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.inventory.showDeviceData(${row.instance})"
          data-tooltip="Network Data"
            ><span class="glyphicon glyphicon-cog"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.inventory.showGitHistory(${row.instance})"
          data-tooltip="Historical"
            ><span class="glyphicon glyphicon-adjust"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.type}', '${row.id}')"
          data-tooltip="Edit"><span class="glyphicon glyphicon-edit">
          </span></button>
        </li>
      </ul>`;
  }
};

tables.link = class LinkTable extends Table {
  addRow(properties) {
    let row = super.addRow(properties);
    row.pools = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'pool', ${row.instance}, {parent: '${this.id}', from: 'links', to: 'pools'})">
      Pools</a></b>`;
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.displayChangelogButton(),
      this.refreshTableButton(),
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.copyTableButton(),
      this.createNewButton(),
      `
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 200px;"
        type="button"
      >
        <select id="link-type-dd-list" class="form-control"></select>
      </button>`,
      this.bulkEditButton(),
      this.exportTableButton(),
      this.bulkDeletionButton(),
    ];
  }

  buttons(row) {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 160px">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.type}', '${
      row.id
    }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.type}', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`;
  }

  postProcessing(...args) {
    super.postProcessing(...args);
    loadTypes("link");
  }
};

tables.pool = class PoolTable extends Table {
  addRelationDisabled = true;

  addRow(properties) {
    let row = super.addRow(properties);
    row.objectNumber = "";
    for (const model of ["device", "link"]) {
      row.objectNumber += `${row[`${model}_number`]} ${model}s`;
      if (model !== "link") row.objectNumber += " - ";
      row[`${model}s`] = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
        '${model}', ${row.instance}, {parent: '${this.id}', from: 'pools',
        to: '${model}s'})">${model.charAt(0).toUpperCase() + model.slice(1)}s</a></b>`;
    }
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.displayChangelogButton(),
      this.refreshTableButton(),
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.copyTableButton(),
      this.createNewButton(),
      this.exportTableButton(),
      ` <button
        class="btn btn-primary"
        onclick="eNMS.inventory.updatePools()"
        data-tooltip="Update all pools"
        type="button"
      >
        <span class="glyphicon glyphicon-flash"></span>
      </button>`,
      ` <button
        type="button"
        class="btn btn-success"
        onclick="eNMS.automation.showRunServicePanel(
          {tableId: '${this.id}', type: '${this.type}'}
        )"
        data-tooltip="Run service on all pools in table"
      >
        <span class="glyphicon glyphicon-play"></span>
      </button>`,
      this.bulkDeletionButton(),
    ];
  }

  buttons(row) {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 230px">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.inventory.updatePools('${row.id}')"
          data-tooltip="Update"><span class="glyphicon glyphicon-refresh">
          </span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('pool', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('pool', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.automation.showRunServicePanel({instance: ${row.instance}})"
          data-tooltip="Run Service"><span class="glyphicon glyphicon-play">
          </span></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>
    `;
  }
};

tables.service = class ServiceTable extends Table {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    row.name = buildServiceLink(row);
    for (const model of ["device", "pool"]) {
      row[`${model}s`] = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
        '${model}', ${row.instance}, {parent: '${this.id}', from: 'target_services',
        to: 'target_${model}s'})">${model.charAt(0).toUpperCase() + model.slice(1)}s
        </a></b>`;
    }
    row["runs"] = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'run', ${row.instance}, {parent: '${this.id}', from: 'services',
      to: 'runs'})">Runs</a></b>`;
    return row;
  }

  get filteringConstraints() {
    const relationFiltering = this.relation ? "false" : "true";
    const parentFiltering = $("#parent-filtering").val() || relationFiltering;
    return {
      soft_deleted: "bool-false",
      workflows_filter: parentFiltering == "true" ? "empty" : "union",
      ...this.userDisplayConstraints,
    };
  }

  get controls() {
    return [
      this.columnDisplay(),
      `
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 240px;"
        type="button"
      >
        <select
          id="parent-filtering"
          name="parent-filtering"
          class="form-control"
        >
          <option value="true">Display top-level services</option>
          <option value="false">Display all services</option>
        </select>
      </button>`,
      this.displayChangelogButton(),
      this.userFilteringButton(),
      `
      <button
        class="btn btn-info"
        onclick="eNMS.table.refreshTable('service', true)"
        data-tooltip="Refresh"
        type="button"
      >
        <span class="glyphicon glyphicon-refresh"></span>
      </button>`,
      `
      <button
        class="btn btn-info"
        id="service-serialized-search-btn"
        onclick="eNMS.table.serializedSearch('service')"
        data-tooltip="Search across all properties"
        type="button"
      >
        <span class="glyphicon glyphicon-search"></span>
      </button>`,
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.copyTableButton(),
      this.createNewButton(),
      `
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 200px;"
        type="button"
      >
        <select id="service-type-dd-list" class="form-control"></select>
      </button>`,
      this.bulkEditButton(),
      this.exportTableButton(),
      this.bulkDeletionButton(),
      this.serializedSearchField(),
    ];
  }

  buttons(row) {
    let runtimeArg = "";
    if (row.type != "workflow") runtimeArg = ", null, 'result'";
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 350px">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('logs', ${row.instance})"
          data-tooltip="Logs">
            <span class="glyphicon glyphicon-list"></span>
          </button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('results', ${row.instance}
          ${runtimeArg})" data-tooltip="Results">
            <span class="glyphicon glyphicon-list-alt"></span>
          </button>
        </li>
        <li>
          <button
            type="button"
            class="btn btn-sm btn-primary"
            onclick="eNMS.base.showInstancePanel('${row.type}', '${row.id}')"
            data-tooltip="Edit"
          ><span class="glyphicon glyphicon-edit"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.type}', '${row.id}',
          'duplicate')" data-tooltip="Duplicate">
          <span class="glyphicon glyphicon-duplicate"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.automation.runService({id: '${row.id}',
          parametrization: ${row.mandatory_parametrization}})"
          data-tooltip="Run"><span class="glyphicon glyphicon-play"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.automation.runService({id: '${row.id}',
          parametrization: true})" data-tooltip="Parameterized Run">
            <span class="glyphicon glyphicon-play-circle"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>
    `;
  }

  postProcessing(...args) {
    let self = this;
    if (this.relation) {
      $("#parent-filtering")
        .val("false")
        .selectpicker("refresh");
    }
    this.createfilteringTooltip("serialized");
    super.postProcessing(...args);
    loadTypes("service");
    let timer = false;
    document.getElementById("serialized-search").addEventListener("keyup", function() {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        self.table.page(0).ajax.reload(null, false);
      }, 500);
    });
    $("#parent-filtering")
      .selectpicker()
      .on("change", function() {
        self.table.page(0).ajax.reload(null, false);
      });
  }
};

tables.run = class RunTable extends Table {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    if (row.service_properties.type == "workflow") {
      const rowLink = `/workflow_builder/${row.url}/${row.runtime}`;
      row.name = `<b><a href="${rowLink}">${row.name}</a></b>`;
    }
    for (const model of ["device", "pool"]) {
      row[`${model}s`] = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
        '${model}', ${row.instance}, {parent: '${this.id}', from: 'runs',
        to: 'target_${model}s'})">${model.charAt(0).toUpperCase() + model.slice(1)}s
        </a></b>`;
    }
    row[`services`] = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'service', ${row.instance}, {parent: '${this.id}', from: 'runs',
      to: 'services'})">Services</a></b>`;
    if (row.server_properties) {
      row.server_name = `<b><a href="#" onclick="eNMS.base.showInstancePanel(
        'server', '${row.server_properties.id}')">${row.server_properties.name}
        </a></b>`;
    }
    if (row.worker_properties) {
      row.worker_name = `<b><a href="#" onclick="eNMS.base.showInstancePanel(
        'worker', '${row.worker_properties.id}')">${row.worker_properties.name}
        </a></b>`;
    }
    row.service = JSON.stringify(row.service_properties).replace(/"/g, "'");
    row.buttons = this.buttons(row);
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.userFilteringButton(),
      this.refreshTableButton(),
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      ` <button
        class="btn btn-info"
        onclick="eNMS.automation.displayCalendar('run')"
        data-tooltip="Calendar"
        type="button"
      >
        <span class="glyphicon glyphicon-calendar"></span>
      </button>`,
      this.exportTableButton(),
    ];
  }

  get filteringConstraints() {
    return this.userDisplayConstraints;
  }

  get tableOrdering() {
    return [0, "desc"];
  }

  buttons(row) {
    return [
      `<ul class="pagination pagination-lg" style="margin: 0px; width: 150px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('logs', ${row.service},
          '${row.runtime}')" data-tooltip="Logs">
          <span class="glyphicon glyphicon-list"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('report', ${row.service},
          '${row.runtime}')" data-tooltip="Report">
          <span class="glyphicon glyphicon-modal-window"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('results', ${row.service},
          '${row.runtime}')" data-tooltip="Results">
          <span class="glyphicon glyphicon-list-alt"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick="eNMS.automation.stopRun('${row.runtime}')"
          data-tooltip="Stop Run">
            <span class="glyphicon glyphicon-stop"></span>
          </button>
        </li>
      </ul>`,
    ];
  }
};

tables.result = class ResultTable extends Table {
  addRow({ properties, tableId }) {
    const status = properties.success;
    delete properties.success;
    delete properties.result;
    let row = super.addRow({
      properties: properties,
      tableId: tableId,
      derivedProperties: ["service_name", "device_name"],
    });
    row.status = status;
    row.success = `
      <button
        type="button"
        class="btn btn-${status ? "success" : "danger"} btn-sm"
        style="width:100%">${status ? "Success" : "Failure"}
      </button>`;
    row.v1 = `<input type="radio" name="v1-${tableId}" value="${row.id}">`;
    row.v2 = `<input type="radio" name="v2-${tableId}" value="${row.id}">`;
    return row;
  }

  get controls() {
    const id =
      this.constraints.parent_service_id ||
      this.constraints.service_id ||
      this.constraints.device_id;
    return [
      this.columnDisplay(),
      `<button
        class="btn btn-info"
        onclick="eNMS.base.displayDiff('${this.type}', ${id})"
        data-tooltip="Compare"
        type="button"
      >
        <span class="glyphicon glyphicon-adjust"></span>
      </button>`,
      this.refreshTableButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
    ];
  }

  get tableOrdering() {
    return [0, "desc"];
  }

  buttons(row) {
    return [
      `
    <ul class="pagination pagination-lg" style="margin: 0px; width: 90px">
      <li>
        <button type="button" class="btn btn-sm btn-info"
        onclick="eNMS.automation.showResult('${row.id}')"
        data-tooltip="Results"><span class="glyphicon glyphicon-list-alt">
        </span></button>
      </li>
      <li>
        <button
          type="button"
          id="btn-result-${row.id}"
          class="btn btn-sm btn-info"
          onclick="eNMS.automation.copyClipboard(
            'btn-result-${row.id}', ${row.instance}
          )"
          data-tooltip="Copy to clipboard"
        ><span class="glyphicon glyphicon-copy"></span></button>
      </li>
    </ul>`,
    ];
  }
};

tables.full_result = class FullResultTable extends tables.result {
  get filteringData() {
    return { full_result: true };
  }

  get modelFiltering() {
    return "result";
  }
};

tables.device_result = class DeviceResultTable extends tables.result {
  get modelFiltering() {
    return "result";
  }
};

tables.task = class TaskTable extends Table {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    if (row.scheduling_mode == "standard") {
      row.periodicity = `${row.frequency} ${row.frequency_unit}`;
    } else {
      row.periodicity = row.crontab_expression;
    }
    for (const model of ["device", "pool"]) {
      row[`${model}s`] = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
        '${model}', ${row.instance}, {parent: '${this.id}', from: 'tasks',
        to: '${model}s'})">${model.charAt(0).toUpperCase() + model.slice(1)}s</a></b>`;
    }
    row["runs"] = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'run', ${row.instance}, {parent: '${this.id}', from: 'task',
      to: 'runs'})">Runs</a></b>`;
    row.service_name = buildServiceLink(row.service_properties);
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.displayChangelogButton(),
      this.userFilteringButton(),
      this.refreshTableButton(),
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      ` <button
        class="btn btn-info"
        onclick="eNMS.automation.displayCalendar('task')"
        data-tooltip="Calendar"
        type="button"
      >
        <span class="glyphicon glyphicon-calendar"></span>
      </button>`,
      this.createNewButton(),
      this.bulkEditButton(),
      this.exportTableButton(),
      ` <button
        type="button"
        class="btn btn-success"
        onclick="eNMS.automation.schedulerAction('resume')"
        data-tooltip="Bulk Resume"
      >
        <span class="glyphicon glyphicon-play"></span>
      </button>
      <button
        type="button"
        class="btn btn-danger"
        onclick="eNMS.automation.schedulerAction('pause')"
        data-tooltip="Bulk Pause"
      >
        <span class="glyphicon glyphicon-pause"></span>
      </button>`,
      this.bulkDeletionButton(),
    ];
  }

  get filteringConstraints() {
    return this.userDisplayConstraints;
  }

  buttons(row) {
    const state = row.is_active ? ["disabled", "active"] : ["active", "disabled"];
    return [
      `<ul class="pagination pagination-lg" style="margin: 0px; width: 230px">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('task', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('task', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate">
          <span class="glyphicon glyphicon-duplicate"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success ${state[0]}" ${state[0]}
          onclick="eNMS.automation.resumeTask('${row.id}')" data-tooltip="Play"
            ><span class="glyphicon glyphicon-play"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger ${state[1]}" ${state[1]}
          onclick="eNMS.automation.pauseTask('${row.id}')" data-tooltip="Pause"
            ><span class="glyphicon glyphicon-pause"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

tables.group = class GroupTable extends Table {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    row.users = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'user', ${row.instance}, {parent: '${this.id}', from: 'groups', to: 'users'})">
      Users</a></b>`;
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.displayChangelogButton(),
      this.refreshTableButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.copyTableButton(),
      this.createNewButton(),
      this.bulkEditButton(),
      this.exportTableButton(),
      ` <button
        class="btn btn-primary"
        onclick="eNMS.administration.updateDeviceRbac()"
        data-tooltip="Update Device RBAC from Pools"
        type="button"
      >
        <span class="glyphicon glyphicon-flash"></span>
      </button>`,
      this.bulkDeletionButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('group', '${
            row.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('group', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

tables.user = class UserTable extends Table {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    row.groups = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'group', ${row.instance}, {parent: '${this.id}', from: 'users', to: 'groups'})">
      Groups</a></b>`;
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.displayChangelogButton(),
      this.refreshTableButton(),
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.copyTableButton(),
      this.createNewButton(),
      this.bulkEditButton(),
      this.exportTableButton(),
      this.bulkDeletionButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('user', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('user', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

tables.credential = class CredentialTable extends Table {
  get controls() {
    return [
      this.columnDisplay(),
      this.displayChangelogButton(),
      this.refreshTableButton(),
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.createNewButton(),
      this.bulkEditButton(),
      this.exportTableButton(),
      this.bulkDeletionButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('credential', '${row.id}')"
          data-tooltip="Edit"><span class="glyphicon glyphicon-edit"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('credential', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

tables.data = class DataTable extends Table {
  get controls() {
    const status = currentStore ? "" : "disabled";
    return [
      this.columnDisplay(),
      this.displayChangelogButton("data"),
      this.refreshTableButton(),
      this.clearSearchButton(),
      `
      <a
        id="upward-store-btn"
        class="btn btn-info ${status}"
        onclick="eNMS.administration.enterStore({parent: true})"
        type="button"
      >
        <span class="glyphicon glyphicon-chevron-up"></span>
      </a>`,
      this.createNewButton(),
      this.bulkEditButton(),
      this.exportTableButton(),
      this.bulkDeletionButton(),
      `<div id="current-store-path" style="margin-top: 9px; margin-left: 9px"></div>`,
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        ${this.rowButtons(row).join("")}
      </ul>`,
    ];
  }

  rowButtons(row) {
    return [
      `<li>
        <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.base.copyToClipboard({text: '${row.persistent_id}' })"
          data-tooltip="Copy Persistent ID to clipboard"
        >
          <span class="glyphicon glyphicon-copy"></span>
        </button>
      </li>`,
      `<li>
        <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.type}', '${row.id}')"
          data-tooltip="Edit"
        >
          <span class="glyphicon glyphicon-edit"></span>
        </button>
      </li>`,
      this.deleteInstanceButton(row),
    ];
  }

  postProcessing(...args) {
    super.postProcessing(...args);
    displayStorePath();
  }
};

tables.snippet = class SnippetTable extends Table {
  get controls() {
    return [
      this.columnDisplay(),
      this.displayChangelogButton(),
      this.refreshTableButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.createNewButton(),
      this.bulkEditButton(),
      this.exportTableButton(),
      `
      <button
        class="btn btn-success"
        onclick="eNMS.administration.openDebugPanel()"
        data-tooltip="Run Debug Snippet"
        type="button"
      >
        <span class="glyphicon glyphicon-play"></span>
      </button>`,
      this.bulkDeletionButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('snippet', '${
            row.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('snippet', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.administration.runDebugCode(${row.id})"
          data-tooltip="Run Snippet"><span class="glyphicon glyphicon-play"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

tables.server = class ServerTable extends Table {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    row.runs = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'run', ${row.instance}, {parent: '${this.id}', from: 'server', to: 'runs'})">
      Runs</a></b>`;
    row.sessions = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'session', ${row.instance}, {parent: '${this.id}', from: 'server', to: 'sessions'})">
      Sessions</a></b>`;
    row.workers = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'worker', ${row.instance}, {parent: '${this.id}', from: 'server', to: 'workers'})">
      Workers</a></b>`;
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.displayChangelogButton(),
      this.refreshTableButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.createNewButton(),
      this.bulkEditButton(),
      this.exportTableButton(),
      this.bulkDeletionButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        ${this.changelogButton(row)}
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('server', '${
            row.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('server', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

tables.changelog = class ChangelogTable extends Table {
  addRelationDisabled = true;

  get controls() {
    return [
      this.columnDisplay(),
      this.refreshTableButton(),
      this.bulkFilteringButton(),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      this.createNewButton(),
      this.exportTableButton(),
    ];
  }

  get tableOrdering() {
    return [0, "desc"];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.administration.showChangelogDiff(${row.id})"
          data-tooltip="Diff"
            ><span class="glyphicon glyphicon-adjust"></span
          ></button>
        </li>
        <li>
          <button ${row.target_id ? "" : "disabled"} type="button"
          class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('${row.target_type}', '${
        row.target_id
      }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
      </ul>`,
    ];
  }
};

tables.session = class SessionTable extends Table {
  get controls() {
    return [
      this.columnDisplay(),
      `<input
        name="context-lines"
        id="slider"
        class="slider"
        style="width: 200px"
      >`,
      this.refreshTableButton("session"),
      this.bulkFilteringButton(),
    ];
  }

  postProcessing(...args) {
    super.postProcessing(...args);
    $("#slider")
      .bootstrapSlider({
        value: 0,
        ticks: [...Array(6).keys()],
        formatter: (value) => `Lines of context: ${value}`,
        tooltip: "always",
      })
      .on("change", function() {
        refreshTable("session");
      });
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.inventory.showSessionLog(${row.id})" data-tooltip="Session Log"
            ><span class="glyphicon glyphicon-list"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('session', '${row.id}')"
          data-tooltip="Edit"><span class="glyphicon glyphicon-edit"></span></button>
        </li>
      </ul>`,
    ];
  }
};

tables.file = class FileTable extends Table {
  addRow(properties) {
    let row = super.addRow(properties);
    if (row.type == "folder") {
      row.filename = `<a href="#" onclick="eNMS.administration.enterFolder
        ({ folder: '${row.filename}'})">
          <span class="glyphicon glyphicon-folder-open" style="margin-left: 8px"></span>
          <b style="margin-left: 6px">${row.filename}</b>
        </a>`;
    } else {
      row.filename = `
        <span class="glyphicon glyphicon-file" style="margin-left: 8px"></span>
        <span style="margin-left: 3px">${row.filename}</span>`;
    }
    return row;
  }

  get controls() {
    const status = folderPath == "" ? "disabled" : "";
    return [
      this.columnDisplay(),
      `
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 240px;"
        type="button"
      >
        <select
          id="parent-filtering"
          name="parent-filtering"
          class="form-control"
        >
          <option value="true">Hierarchical Display</option>
          <option value="false">Flat Display</option>
        </select>
      </button>`,
      this.refreshTableButton("file"),
      this.copySearchLinkButton(),
      this.clearSearchButton(),
      `
      <a
        id="upward-folder-btn"
        class="btn btn-info ${status}"
        onclick="eNMS.administration.enterFolder({parent: true})"
        type="button"
      >
        <span class="glyphicon glyphicon-chevron-up"></span>
      </a>`,
      `
      <button
        class="btn btn-primary parent-filtering"
        onclick="eNMS.base.showInstancePanel('folder')"
        data-tooltip="Create New Folder"
        type="button"
      >
        <span class="glyphicon glyphicon-folder-open"></span>
      </button>`,
      ` <button
        class="btn btn-primary parent-filtering"
        onclick="eNMS.administration.showFileUploadPanel()"
        data-tooltip="Upload Files"
        type="button"
      >
        <span class="glyphicon glyphicon-import"></span>
      </button>`,
      ` <button
        class="btn btn-primary"
        onclick="eNMS.administration.scanFolder()"
        data-tooltip="Scan Folder"
        type="button"
      >
        <span class="glyphicon glyphicon-flash"></span>
      </button>`,
      this.bulkEditButton(),
      this.bulkDeletionButton(),
      `<div id="current-folder-path" style="margin-top: 9px; margin-left: 9px"></div>`,
    ];
  }

  copyClipboardButton(row) {
    return `
      <li>
        <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.base.copyToClipboard({text: '${row.path}' })"
          data-tooltip="Copy Path to clipboard"
        >
          <span class="glyphicon glyphicon-copy"></span>
        </button>
      </li>`;
  }

  downloadButton(row) {
    return `
      <li>
        <button
          type="button"
          class="btn btn-sm btn-info"
          onclick="location.href='/download/${row.type}/${row.path.slice(1)}'"
          data-tooltip="Download File"
        >
          <span class="glyphicon glyphicon-export"></span>
        </button>
      </li>`;
  }

  editButton(row) {
    return `
      <li>
        <button type="button" class="btn btn-sm btn-primary"
        onclick="eNMS.base.showInstancePanel(
          '${row.type}', '${row.id}')" data-tooltip="Edit"
          ><span class="glyphicon glyphicon-edit"></span
        ></button>
      </li>`;
  }

  buttons(row) {
    if (row.type == "folder") {
      return [
        `
        <ul class="pagination pagination-lg" style="margin: 0px;">
          ${this.changelogButton(row)}
          ${this.copyClipboardButton(row)}
          ${this.downloadButton(row)}
          ${this.editButton(row)}
          <button type="button"
            class="btn btn-sm btn-primary"
            onclick="eNMS.administration.showFileUploadPanel('${row.path}')"
            data-tooltip="Upload Files in Folder"
          >
            <span class="glyphicon glyphicon-import"></span>
          </button>
          ${this.deleteInstanceButton(row)}
        </ul>
        `,
      ];
    } else {
      return [
        `
        <ul class="pagination pagination-lg" style="margin: 0px;">
          ${this.changelogButton(row)}
          ${this.copyClipboardButton(row)}
          ${this.downloadButton(row)}
          ${this.editButton(row)}
          <li>
            <button type="button" class="btn btn-sm btn-primary"
            onclick="eNMS.administration.editFile(
              '${row.id}', '${row.name}', '${row.path}')" data-tooltip="File Content">
              <span class="glyphicon glyphicon-pencil"></span>
            </button>
          </li>
          ${this.deleteInstanceButton(row)}
        </ul>`,
      ];
    }
  }

  get filteringConstraints() {
    const parentFiltering = ($("#parent-filtering").val() || "true") == "true";
    if (parentFiltering) {
      const fileFolderPath = settings.paths.files || filePath;
      const fullPath = `${fileFolderPath}${folderPath}`;
      return { folder_path: fullPath, folder_path_filter: "equality" };
    } else {
      return {};
    }
  }

  postProcessing(...args) {
    let self = this;
    super.postProcessing(...args);
    displayFolderPath(folderPath);
    $("#parent-filtering")
      .selectpicker()
      .on("change", function() {
        self.table.page(0).ajax.reload(null, false);
        $("#current-folder-path,.parent-filtering").toggle();
      });
  }
};

tables.worker = class WorkerTable extends Table {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    row.runs = `<b><a href="#" onclick="eNMS.table.displayRelationTable(
      'run', ${row.instance}, {parent: '${this.id}', from: 'worker', to: 'runs'})">
      Runs</a></b>`;
    if (row.server_properties) {
      row.server_name = `<b><a href="#" onclick="eNMS.base.showInstancePanel(
        'server', '${row.server_properties.id}')">${row.server_properties.name}
        </a></b>`;
    }
    return row;
  }

  get controls() {
    return [this.columnDisplay(), this.refreshTableButton(), this.clearSearchButton()];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showInstancePanel('worker', '${
            row.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

export const clearSearch = function(tableId, notification) {
  $(`.search-input-${tableId},.search-list-${tableId}`).val("");
  $(".search-relation-dd")
    .val("any")
    .selectpicker("refresh");
  $(".search-relation")
    .val([])
    .trigger("change");
  $(`.search-select-${tableId}`).val("inclusion");
  if ($("#serialized-search-div").is(":visible")) {
    $("#serialized-search").val("");
    $("#serialized-search-div").toggle();
  }
  refreshTable(tableId);
  if (notification) notify("Search parameters cleared.", "success", 5);
};

function copySelectionToClipboard(tableId) {
  let table = tableInstances[tableId];
  table.copyClipboard = true;
  refreshTable(tableId);
}

function copySearchLinkToClipboard(tableId) {
  const { columns, ...data } = tableInstances[tableId].data;
  const query = new URLSearchParams({ search: JSON.stringify(data) }).toString();
  const fullUrl = `${window.location.origin}${window.location.pathname}?${query}`;
  copyToClipboard({ text: fullUrl, includeText: false });
}

function buildServiceLink(service) {
  if (service.type == "workflow") {
    return `<b><a href="/workflow_builder/${service.builder_link}">${sanitize(
      service.name
    )}</a></b>`;
  } else if (service.builder_link) {
    return (
      service.name.substring(0, service.name.lastIndexOf(service.scoped_name)) +
      `<b><a href="/workflow_builder/${service.builder_link}">${sanitize(
        service.scoped_name
      )}</a></b>`
    );
  } else {
    return service.name;
  }
}

function exportTable(tableId) {
  let table = tableInstances[tableId];
  table.csvExport = true;
  refreshTable(tableId);
}

function userFilteringDisplay(tableId) {
  let table = tableInstances[tableId];
  table.userFiltering = table.userFiltering == "user" ? "users" : "user";
  localStorage.setItem(`userFiltering-${table.type}`, table.userFiltering);
  $(`#user-filtering-icon-${tableId}`).attr("class", `fa fa-${table.userFiltering}`);
  refreshTable(tableId);
}

function showTableChangelogPanel(tableId, tableType) {
  const type = tableType || tableInstances[tableId].type;
  const constraints = { [`${type}_filter`]: "empty", [`${type}_invert`]: true };
  showChangelogPanel(tableId, constraints);
}

export const refreshTable = function(tableId, notification, updateParent, firstPage) {
  if (!$(`#table-${tableId}`).length) return;
  const table = tableInstances[tableId].table;
  table.page(firstPage ? 0 : table.page()).ajax.reload(null, false);
  const parentTable = tableInstances[tableId].relation?.relation?.parent;
  if (updateParent && parentTable) refreshTable(parentTable);
  if (notification) notify("Table refreshed.", "success", 5);
};

function refreshTablePeriodically(tableId, interval, first) {
  if (userIsActive && document.hasFocus() && !first) refreshTable(tableId, false);
  setTimeout(() => refreshTablePeriodically(tableId, interval), interval);
}

function showBulkDeletionPanel(tableId, model) {
  showConfirmationPanel({
    id: `bulk-${model}-${tableId}`,
    title: "Bulk Deletion (delete all items in table)",
    message: `Are you sure you want to delete all items
      currently displayed in the table ?`,
    confirmButton: "Delete",
    onConfirm: () => bulkDeletion(tableId, model),
  });
}

function showBulkEditPanel(formId, model, tableId, number) {
  showConfirmationPanel({
    id: `bulk-edit-${tableId}`,
    title: `Bulk edit all ${number} ${model}s `,
    message: `Are you sure to edit the ${number} ${model}s
      in the table ?`,
    confirmButton: "Edit",
    onConfirm: () => bulkEdit(formId, model, tableId),
  });
}

function bulkDeletion(tableId, model) {
  call({
    url: `/bulk_deletion/${model}`,
    data: tableInstances[tableId].getFilteringData(),
    callback: function(number) {
      refreshTable(tableId, false, true);
      notify(`${number} items deleted.`, "success", 5, true);
    },
  });
}

function bulkRemoval(tableId, model, instance) {
  const relation = `${instance.type}/${instance.id}/${instance.relation.to}`;
  call({
    url: `/bulk_removal/${model}/${relation}`,
    data: tableInstances[tableId].getFilteringData(),
    callback: function(number) {
      refreshTable(tableId, false, true);
      notify(
        `${number} ${model}s removed from ${instance.type} '${instance.name}'.`,
        "success",
        5,
        true
      );
    },
  });
}

function bulkEdit(formId, model, tableId) {
  call({
    url: `/bulk_edit/${model}`,
    form: `${formId}-form-${tableId}`,
    callback: function(number) {
      refreshTable(tableId);
      $(`#${formId}-${tableId}`).remove();
      notify(`${number} items modified.`, "success", 5, true);
    },
  });
}

function displayRelationTable(type, instance, relation) {
  openPanel({
    name: "table",
    content: `
      <div class="modal-body">
        <div id="tooltip-overlay" class="overlay"></div>
        <form
          id="search-form-${type}-${instance.id}"
          class="form-horizontal form-label-left"
          method="post"
        >
          <nav
            id="controls-${type}-${instance.id}"
            class="navbar navbar-default nav-controls"
            role="navigation"
          ></nav>
          <table
            id="table-${type}-${instance.id}"
            class="table table-striped table-bordered table-hover"
            cellspacing="0"
            width="100%"
          ></table>
        </form>
      </div>`,
    id: instance.id,
    size: "1300 600",
    title: `${instance.name} - ${type}s`,
    tableId: `${type}-${instance.id}`,
    callback: function() {
      const constraints = { [`${relation.from}`]: [instance.name] };
      // eslint-disable-next-line new-cap
      new tables[type](instance.id, constraints, { relation, ...instance });
    },
  });
}

function serializedSearch(type) {
  $("#serialized-search-div").toggle();
  $(`#${type}-serialized-search-btn`).toggleClass("btn-pressed");
  if (!$("#serialized-search-div").is(":visible")) {
    $("#serialized-search").val("");
    refreshTable(type);
  } else {
    $("#serialized-search").focus();
  }
  tableInstances[type].createfilteringTooltip("serialized");
}

function togglePaginationDisplay(tableId) {
  const table = tableInstances[tableId];
  table.displayPagination = !table.displayPagination;
  refreshTable(tableId);
}

for (const [type, table] of Object.entries(tables)) {
  table.prototype.type = type;
}

configureNamespace("table", [
  bulkDeletion,
  bulkEdit,
  bulkRemoval,
  clearSearch,
  copySelectionToClipboard,
  copySearchLinkToClipboard,
  displayRelationTable,
  exportTable,
  refreshTable,
  serializedSearch,
  showBulkDeletionPanel,
  showBulkEditPanel,
  showTableChangelogPanel,
  togglePaginationDisplay,
  userFilteringDisplay,
]);
