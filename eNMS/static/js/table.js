/*
global
tableProperties: false
*/

import {
  configureNamespace,
  createTooltip,
  createTooltips,
  downloadFile,
  notify,
  serializeForm,
  userIsActive,
} from "./base.js";
import { loadServiceTypes } from "./automation.js";

export let tables = {};
export let tableInstances = {};
export const models = {};
let waitForSearch = false;

$.fn.dataTable.ext.errMode = "none";

export class Table {
  constructor(type, instance, runtime, id) {
    let self = this;
    this.instance = instance;
    this.runtime = runtime;
    this.type = type;
    this.columns = tableProperties[this.type];
    let visibleColumns = localStorage.getItem(`table/${this.type}`);
    if (visibleColumns) visibleColumns = visibleColumns.split(",");
    this.columns.forEach((column) => {
      if (visibleColumns) column.visible = visibleColumns.includes(column.data);
      column.name = column.data;
    });
    this.id = `${this.type}${id ? `-${id}` : ""}`;
    tableInstances[this.id] = this;
    // eslint-disable-next-line new-cap
    this.table = $(`#table-${this.id}`).DataTable({
      serverSide: true,
      orderCellsTop: true,
      autoWidth: false,
      scrollX: true,
      drawCallback: function () {
        $(".paginate_button > a").on("focus", function () {
          $(this).blur();
        });
        createTooltips();
      },
      sDom: "tilp",
      columns: this.columns,
      columnDefs: [{ className: "dt-center", targets: "_all" }],
      initComplete: function () {
        this.api()
          .columns()
          .every(function (index) {
            const data = self.columns[index];
            let element;
            const elementId = `${self.type}_filtering-${data.data}`;
            if (data.search == "text") {
              element = `
              <div class="input-group" style="width:100%">
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
                <select
                  id="${elementId}"
                  name="${data.data}"
                  class="form-control search-list-${self.id}"
                  style="width: 100%; height: 30px; margin-top: 5px"
                >
                  <option value="">Any</option>
                  <option value="bool-true">True</option>
                  <option value="bool-false">False</option>
                </select>`;
            }
            $(element)
              .appendTo($(this.header()))
              .on("keyup change", function () {
                if (waitForSearch) return;
                waitForSearch = true;
                setTimeout(function () {
                  self.table.page(0).ajax.reload(null, false);
                  waitForSearch = false;
                }, 500);
              })
              .on("click", function (e) {
                e.stopPropagation();
              });
          });
        $(`#controls-${self.id}`).html(self.controls);
        self.postProcessing();
      },
      ajax: {
        url: `/filtering/${this.modelFiltering || this.type}`,
        type: "POST",
        contentType: "application/json",
        data: (d) => {
          Object.assign(d, {
            form: serializeForm(`#search-form-${this.id}`),
            instance: this.instance,
            columns: this.columns,
            type: this.type,
            export: self.csvExport,
          });
          Object.assign(d, self.filteringData);
          if (this.runtime) {
            d.runtime = $(`#runtimes-${this.instance.id}`).val() || this.runtime;
          }
          return JSON.stringify(d);
        },
        dataSrc: function (result) {
          if (result.error) {
            notify(result.error, "error", 5);
            return [];
          }
          if (self.csvExport) {
            self.exportTable(result.full_result);
            self.csvExport = false;
          }
          return result.data.map((instance) =>
            self.addRow({ properties: instance, tableId: self.id })
          );
        },
      },
    });
    $(window).resize(this.table.columns.adjust);
    if (["changelog", "run", "result"].includes(this.type)) {
      this.table.order([0, "desc"]).draw();
    }
    if (["run", "service", "task", "workflow"].includes(this.type)) {
      refreshTablePeriodically(this.id, 3000, true);
    }
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
      return visibleColumns.map((column) => instance[column]);
    });
    downloadFile(
      this.type,
      [visibleColumns, ...result].map((e) => e.join(",")).join("\n"),
      "csv"
    );
  }

  postProcessing() {
    let self = this;
    if ($(`#advanced-search-${this.type}`).length) {
      createTooltip({
        autoshow: true,
        persistent: true,
        name: `${this.type}_relation_filtering`,
        target: `#advanced-search-${this.type}`,
        container: `#controls-${this.type}`,
        position: {
          my: "center-top",
          at: "center-bottom",
          offsetY: 18,
        },
        url: `../form/${this.type}_relation_filtering`,
        title: "Relationship-based Filtering",
      });
    }
    this.createfilteringTooltips();
    createTooltips();
    const visibleColumns = localStorage.getItem(`table/${this.type}`);
    this.columns.forEach((column) => {
      const visible = visibleColumns
        ? visibleColumns.split(",").includes(column.name)
        : "visible" in column
        ? column.visible
        : true;
      $("#column-display").append(
        new Option(column.title || column.data, column.data, visible, visible)
      );
    });
    $("#column-display").selectpicker("refresh");
    $("#column-display").on("change", function () {
      self.columns.forEach((col) => {
        self.table.column(`${col.name}:name`).visible($(this).val().includes(col.data));
      });
      self.table.ajax.reload(null, false);
      self.createfilteringTooltips();
      localStorage.setItem(`table/${self.type}`, $(this).val());
    });
    self.table.columns.adjust();
  }

  createfilteringTooltips() {
    this.columns.forEach((column) => {
      if (column.search != "text") return;
      const elementId = `${this.type}_filtering-${column.data}`;
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
          <select
            id="${column.data}_filter"
            name="${column.data}_filter"
            class="form-control search-select-${this.id}"
            style="width: 100%; height: 30px; margin-top: 15px"
          >
            <option value="inclusion">Inclusion</option>
            <option value="equality">Equality</option>
            <option value="regex">Regular Expression</option>
          </select>
        </div>`,
      });
    });
  }

  columnDisplay() {
    return `
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 200px;"
        type="button"
      >
        <select multiple
          id="column-display"
          title="Columns"
          class="form-control"
          data-actions-box="true"
          data-selected-text-format="static"
        ></select>
      </button>`;
  }

  createNewButton() {
    return `
      <button
        class="btn btn-primary"
        onclick="eNMS.base.showTypePanel('${this.type}')"
        data-tooltip="New"
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

  searchTableButton() {
    return `
      <button
        id="advanced-search-${this.type}"
        class="btn btn-info"
        data-tooltip="Advanced Search"
        type="button"
      >
        <span class="glyphicon glyphicon-search"></span>
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

  deleteInstanceButton(row) {
    return `
      <li>
        <button type="button" class="btn btn-sm btn-danger"
        onclick="eNMS.base.showDeletionPanel(${row.instance})" data-tooltip="Delete"
          ><span class="glyphicon glyphicon-trash"></span
        ></button>
      </li>`;
  }

  addRow({ properties, tableId, derivedProperties }) {
    let row = { tableId: tableId, ...properties };
    row.instanceProperties = {
      id: row.id,
      name: row.dbName || row.name,
      type: row.type,
    };
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
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.createNewButton(),
      this.exportTableButton(),
      this.searchTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
    ];
  }

  buttons(row) {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 230px">
        <li>
          <button type="button" class="btn btn-sm btn-dark"
          onclick="eNMS.inventory.showConnectionPanel(${row.instance})"
          data-tooltip="Connection"
            ><span class="glyphicon glyphicon-console"></span
          ></button>
        </li>
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
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('device', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('device', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`;
  }
};

tables.configuration = class ConfigurationTable extends Table {
  addRow(kwargs) {
    let row = super.addRow({
      derivedProperties: ["last_runtime"],
      ...kwargs,
    });
    return row;
  }

  get modelFiltering() {
    return "device";
  }

  postProcessing(...args) {
    super.postProcessing(...args);
    $("#slider").bootstrapSlider({
      value: 0,
      ticks: [...Array(6).keys()],
      formatter: (value) => `Lines of context: ${value}`,
      tooltip: "always",
    });
    $("#slider").on("change", function () {
      refreshTable("configuration");
    });
  }

  get controls() {
    return [
      this.columnDisplay(),
      `<input
        name="context-lines"
        id="slider"
        class="slider"
        style="width: 200px"
      >`,
      this.clearSearchButton(),
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
          data-tooltip="Historic"
            ><span class="glyphicon glyphicon-adjust"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('device', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
      </ul>`;
  }
};

tables.link = class LinkTable extends Table {
  get controls() {
    return [
      this.columnDisplay(),
      this.createNewButton(),
      this.exportTableButton(),
      this.searchTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
    ];
  }

  buttons(row) {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 120px">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('link', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('link', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`;
  }
};

tables.pool = class PoolTable extends Table {
  addRow(properties) {
    let row = super.addRow(properties);
    row.objectNumber = `${row.device_number} devices - ${row.link_number} links`;
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
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
      this.searchTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
    ];
  }

  buttons(row) {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 230px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.visualization.showPoolView('${row.id}')"
          data-tooltip="Internal View">
          <span class="glyphicon glyphicon-eye-open"></span></button>
        </li>
        <li>
          <button
            type="button"
            class="btn btn-sm btn-primary"
            onclick="eNMS.inventory.showPoolObjectsPanel('${row.id}')"
            data-tooltip="Pool Objects"
          ><span class="glyphicon glyphicon-wrench"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.inventory.updatePools('${row.id}')"
          data-tooltip="Update"><span class="glyphicon glyphicon-refresh">
          </span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('pool', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('pool', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>
    `;
  }
};

tables.service = class ServiceTable extends Table {
  addRow(kwargs) {
    const dbName = kwargs.properties.name;
    delete kwargs.properties.name;
    let row = super.addRow(kwargs);
    row.dbName = dbName;
    row.name =
      row.type === "workflow"
        ? `<b><a href="#" onclick="eNMS.workflow.filterWorkflowTable(
      '${this.id}', ${row.id})">${row.scoped_name}</a></b>`
        : $("#parent-filtering").val() == "true"
        ? row.scoped_name
        : row.dbName;
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      `
      <input type="hidden" id="workflow-filtering" name="workflow-filtering">
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 300px;"
        type="button"
      >
        <select
          id="parent-filtering"
          name="parent-filtering"
          class="form-control"
        >
          <option value="true">Display services hierarchically</option>
          <option value="false">Display all services</option>
        </select>
      </button>
      </input>`,
      this.searchTableButton(),
      this.clearSearchButton(),
      `
      <button
        class="btn btn-info"
        onclick="eNMS.table.refreshTable('service', true)"
        data-tooltip="Refresh"
        type="button"
      >
        <span class="glyphicon glyphicon-refresh"></span>
      </button>
      <a
        id="left-arrow"
        class="btn btn-info disabled"
        onclick="action['Backward']()"
        type="button"
      >
        <span class="glyphicon glyphicon-chevron-left"></span>
      </a>
      <a
        id="right-arrow"
        class="btn btn-info disabled"
        onclick="action['Forward']()"
        type="button"
      >
        <span class="glyphicon glyphicon-chevron-right"></span>
      </a>`,
      this.exportTableButton(),
      `
      <button
        class="btn btn-primary"
        onclick="eNMS.automation.openServicePanel()"
        data-tooltip="New"
        type="button"
      >
        <span class="glyphicon glyphicon-plus"></span>
      </button>
      <button
        style="background:transparent; border:none; 
        color:transparent; width: 200px;"
        type="button"
      >
        <select id="service-type" class="form-control"></select>
      </button>`,
    ];
  }

  buttons(row) {
    let runtimeArg = "";
    if (row.type != "workflow") runtimeArg = ", null, 'result'";
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 270px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('results', ${row.instance}
          ${runtimeArg})" data-tooltip="Results">
            <span class="glyphicon glyphicon-list-alt"></span>
          </button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('logs', ${row.instance})"
          data-tooltip="Logs">
            <span class="glyphicon glyphicon-list"></span>
          </button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.automation.normalRun('${row.id}')" data-tooltip="Run"
            ><span class="glyphicon glyphicon-play"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.base.showTypePanel('${row.type}', '${row.id}', 'run')"
          data-tooltip="Parameterized Run"
            ><span class="glyphicon glyphicon-play-circle"></span
          ></button>
        </li>
        <li>
          <button
            type="button"
            class="btn btn-sm btn-primary"
            onclick="eNMS.base.showTypePanel('${row.type}', '${row.id}')"
            data-tooltip="Edit"
          ><span class="glyphicon glyphicon-edit"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.automation.exportService('${row.id}')" data-tooltip="Export"
            ><span class="glyphicon glyphicon-upload"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>
    `;
  }

  postProcessing(...args) {
    let self = this;
    super.postProcessing(...args);
    loadServiceTypes();
    $("#parent-filtering")
      .selectpicker()
      .on("change", function () {
        self.table.page(0).ajax.reload(null, false);
      });
  }
};

tables.run = class RunTable extends Table {
  addRow(kwargs) {
    let row = super.addRow(kwargs);
    row.service = JSON.stringify(row.service_properties).replace(/"/g, "'");
    row.buttons = this.buttons(row);
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.searchTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
      ` <button
        class="btn btn-info"
        onclick="eNMS.automation.displayCalendar('run')"
        data-tooltip="Calendar"
        type="button"
      >
        <span class="glyphicon glyphicon-calendar"></span>
      </button>`,
    ];
  }

  buttons(row) {
    return [
      `<ul class="pagination pagination-lg" style="margin: 0px; width: 100px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('logs', ${row.service},
          '${row.runtime}')" data-tooltip="Logs">
          <span class="glyphicon glyphicon-list"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('results', ${row.service},
          '${row.runtime}')" data-tooltip="Results">
          <span class="glyphicon glyphicon-list-alt"></span></button>
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
    const instance = JSON.stringify(this.instance).replace(/"/g, "'");
    return [
      `<button
        class="btn btn-info"
        onclick="eNMS.automation.compare('${this.type}', ${instance})"
        data-tooltip="Compare"
        type="button"
      >
        <span class="glyphicon glyphicon-adjust"></span>
      </button>`,
      this.refreshTableButton(),
      this.clearSearchButton(),
    ];
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
    return row;
  }

  get controls() {
    return [
      this.columnDisplay(),
      this.createNewButton(),
      this.searchTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
      ` <button
        class="btn btn-info"
        onclick="eNMS.automation.displayCalendar('task')"
        data-tooltip="Calendar"
        type="button"
      >
        <span class="glyphicon glyphicon-calendar"></span>
      </button>
      <button
        type="button"
        class="btn btn-success"
        onclick="eNMS.automation.schedulerAction('resume')"
        data-tooltip="Resume all tasks"
      >
        <span class="glyphicon glyphicon-play"></span>
      </button>
      <button
        type="button"
        class="btn btn-danger"
        onclick="eNMS.automation.schedulerAction('pause')"
        data-tooltip="Pause all tasks"
      >
        <span class="glyphicon glyphicon-pause"></span>
      </button>`,
    ];
  }

  buttons(row) {
    const state = row.is_active ? ["disabled", "active"] : ["active", "disabled"];
    return [
      `<ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('task', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('task', '${row.id}', 'duplicate')"
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

tables.user = class UserTable extends Table {
  get controls() {
    return [
      this.columnDisplay(),
      this.createNewButton(),
      this.exportTableButton(),
      this.searchTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('user', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('user', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

tables.group = class GroupTable extends Table {
  get controls() {
    return [
      this.columnDisplay(),
      this.createNewButton(),
      this.searchTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('group', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('group', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

tables.access = class AccessTable extends Table {
  get controls() {
    return [
      this.columnDisplay(),
      this.createNewButton(),
      this.searchTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('access', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('access', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>`,
    ];
  }
};

tables.server = class ServerTable extends Table {
  get controls() {
    return [
      this.columnDisplay(),
      this.createNewButton(),
      this.exportTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('server', '${row.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('server', '${row.id}', 'duplicate')"
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
  get controls() {
    return [
      this.columnDisplay(),
      this.createNewButton(),
      this.exportTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
    ];
  }
};

tables.session = class SessionTable extends Table {
  get controls() {
    return [this.columnDisplay(), this.refreshTableButton("session")];
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
      </ul>`,
    ];
  }
};

tables.event = class EventTable extends Table {
  get controls() {
    return [
      this.columnDisplay(),
      this.createNewButton(),
      this.exportTableButton(),
      this.clearSearchButton(),
      this.refreshTableButton(),
    ];
  }

  buttons(row) {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 150px">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('event', '${row.id}')"
          data-tooltip="Edit"><span class="glyphicon glyphicon-edit">
          </span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('event', '${row.id}', 'duplicate')"
          data-tooltip="Duplicate">
          <span class="glyphicon glyphicon-duplicate"></span></button>
        </li>
        ${this.deleteInstanceButton(row)}
      </ul>
    `,
    ];
  }
};

export const clearSearch = function (tableId, notification) {
  $(`.search-input-${tableId},.search-list-${tableId}`).val("");
  $(".search-relation-dd").val("any").selectpicker("refresh");
  $(".search-relation").val([]).trigger("change");
  $(`.search-select-${tableId}`).val("inclusion");
  refreshTable(tableId);
  if (notification) notify("Search parameters cleared.", "success", 5);
};

function exportTable(tableId) {
  let table = tableInstances[tableId];
  table.csvExport = true;
  refreshTable(tableId);
}

export const refreshTable = function (tableId, notification) {
  tableInstances[tableId].table.ajax.reload(null, false);
  if (notification) notify("Table refreshed.", "success", 5);
};

function refreshTablePeriodically(tableId, interval, first) {
  if (userIsActive && !first) refreshTable(tableId, false);
  setTimeout(() => refreshTablePeriodically(tableId, interval), interval);
}

configureNamespace("table", [clearSearch, exportTable, refreshTable]);
