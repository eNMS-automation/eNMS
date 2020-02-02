/*
global
page: false
*/

import {
  configureNamespace,
  createTooltips,
  notify,
  serializeForm,
  userIsActive,
} from "./base.js";
import { loadServiceTypes } from "./automation.js";
import { filterView } from "./visualization.js";

export let tables = {};
export const models = {};

export function initTable(type, instance, runtime, id) {
  // eslint-disable-next-line new-cap
  tables[type] = $(id ? `#${id}` : "#table").DataTable({
    serverSide: true,
    orderCellsTop: true,
    autoWidth: false,
    scrollX: true,
    stateSave: true,
    drawCallback: function() {
      $(".paginate_button > a").on("focus", function() {
        $(this).blur();
      });
      createTooltips();
    },
    sDom: "tilp",
    columns: models[type].columns,
    columnDefs: [{ className: "dt-center", targets: "_all" }],
    initComplete: function() {
      this.api()
        .columns()
        .every(function(index) {
          const data = models[type].columns[index];
          let element;
          if (data.search == "text") {
            element = `
              <input
                id="${type}_filtering-${data.data}"
                name="${data.data}"
                type="text"
                placeholder="&#xF002;"
                class="form-control"
                style="font-family:Arial, FontAwesome; width: 100%;
                height: 30px; margin-top: 5px"
              >`;
          } else if (data.search == "bool") {
            element = `
              <select
                id="${type}_filtering-${data.data}"
                name="${data.data}"
                class="form-control"
                style="width: 100%; height: 30px; margin-top: 5px"
              >
                <option value="">Any</option>
                <option value="bool-true">True</option>
                <option value="bool-false">False</option>
              </select>`;
          }
          $(element)
            .appendTo($(this.header()))
            .on("keyup change", function() {
              tables[type].page(0).ajax.reload(null, false);
            })
            .on("click", function(e) {
              e.stopPropagation();
            });
        });
      $(`#controls-${type}`).html(models[type].controls);
      if (models[type].postProcessing) models[type].postProcessing();
      this.api().columns.adjust();
    },
    ajax: {
      url: `/table_filtering/${models[type].modelFiltering || type}`,
      type: "POST",
      contentType: "application/json",
      data: (d) => {
        const form = $(`#${type}_filtering`).length
          ? `#${type}_filtering-form`
          : `#search-${type}-form`;
        d.form = serializeForm(form);
        d.instance = instance;
        d.columns = models[type].columns;
        d.type = type
        if (runtime) {
          d.runtime = $(`#runtimes-${instance.id}`).val() || runtime;
        }
        return JSON.stringify(d);
      },
      dataSrc: function(result) {
        return result.data.map((instance) => new models[type](instance));
      },
    },
  });
  if (["changelog", "run", "result"].includes(type)) {
    tables[type].order([0, "desc"]).draw();
  }
  if (["run", "service", "task", "workflow"].includes(type)) {
    refreshTablePeriodically(type, 3000, true);
  }
}

function filterTable(formType) {
  if (page.includes("table")) {
    tables[formType].page(0).ajax.reload(null, false);
  } else {
    filterView(formType);
  }
  notify("Filter applied.", "success", 5);
}

export const refreshTable = function(tableType, displayNotification) {
  tables[tableType].ajax.reload(null, false);
  if (displayNotification) notify("Table refreshed.", "success", 5);
};

function refreshTablePeriodically(tableType, interval, first) {
  if (userIsActive && !first) refreshTable(tableType, false);
  setTimeout(() => refreshTablePeriodically(tableType, interval), interval);
}

class Base {
  constructor(properties) {
    Object.assign(this, properties);
    this.instance = JSON.stringify({
      id: this.id,
      name: this.name,
      type: this.type,
    }).replace(/"/g, "'");
  }

  static createNewButton(type) {
    return `
      <button
        class="btn btn-primary"
        onclick="eNMS.base.showTypePanel('${type}')"
        data-tooltip="New"
        type="button"
      >
        <span class="glyphicon glyphicon-plus"></span>
      </button>`;
  }

  static searchTableButton(type) {
    return `
      <button
        class="btn btn-info"
        onclick="eNMS.base.openPanel({name: '${type}_filtering'})"
        data-tooltip="Advanced Search"
        type="button"
      >
        <span class="glyphicon glyphicon-search"></span>
      </button>`;
  }

  static refreshTableButton(type) {
    return `
      <button
        class="btn btn-info"
        onclick="eNMS.table.refreshTable('${type}', true)"
        data-tooltip="Refresh"
        type="button"
      >
        <span class="glyphicon glyphicon-refresh"></span>
      </button>`;
  }

  get deleteInstanceButton() {
    return `
      <li>
        <button type="button" class="btn btn-sm btn-danger"
        onclick="eNMS.base.showDeletionPanel(${
          this.instance
        })" data-tooltip="Delete"
          ><span class="glyphicon glyphicon-trash"></span
        ></button>
      </li>`;
  }

  static get lastModifiedColumn() {
    return {
      data: "last_modified",
      title: "Last modified",
      search: "text",
      render: function(_, __, instance) {
        return instance.last_modified.slice(0, -7);
      },
      width: "150px",
    };
  }
}

models.device = class Device extends Base {
  static get columns() {
    return [
      { data: "name", title: "Name", search: "text" },
      { data: "description", title: "Description", search: "text" },
      { data: "subtype", title: "Subtype", search: "text" },
      { data: "model", title: "Model", search: "text" },
      { data: "location", title: "Location", search: "text" },
      { data: "vendor", title: "Vendor", search: "text" },
      { data: "operating_system", title: "Operating System", search: "text" },
      { data: "os_version", title: "OS Version", search: "text" },
      { data: "ip_address", title: "IP Address", search: "text" },
      { data: "port", title: "Port", search: "text" },
      { data: "buttons" },
    ];
  }

  static get controls() {
    return [
      super.createNewButton("device"),
      ` <button type="button" class="btn btn-primary"
      onclick="eNMS.administration.showImportTopologyPanel()"
      data-tooltip="Export"><span class="glyphicon glyphicon-download">
      </span></button>
      <button type="button" class="btn btn-primary"
      onclick="eNMS.base.openPanel({name: 'excel_export'})" data-tooltip="Export"
        ><span class="glyphicon glyphicon-upload"></span
      ></button>`,
      super.searchTableButton("device"),
      super.refreshTableButton("device"),
    ];
  }

  get buttons() {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 230px">
        <li>
          <button type="button" class="btn btn-sm btn-dark"
          onclick="eNMS.inventory.showConnectionPanel(${this.id})"
          data-tooltip="Connection"
            ><span class="glyphicon glyphicon-console"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.inventory.showDeviceData(${this.instance})"
          data-tooltip="Network Data"
            ><span class="glyphicon glyphicon-cog"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.inventory.showDeviceResultsPanel(${this.instance})"
          data-tooltip="Results"
            ><span class="glyphicon glyphicon-list-alt"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('device', '${
            this.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('device', '${this.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        ${this.deleteInstanceButton}
      </ul>`;
  }
};

models.configuration = class Configuration extends Base {

  static get modelFiltering() {
    return "device";
  }

  static get columns() {
    return [
      { data: "name", title: "Name", search: "text", width: "150px" },
      { data: "configuration", title: "Configuration", search: "text", className: "dt-body-right" },
      { data: "buttons", width: "90px" },
    ];
  }

  static get controls() {
    return `
      <select
        id="data-type"
        name="data-type"
        class="form-control"
      >
        <option value="configuration">Configuration</option>
        <option value="operational_data">Operational Data</option>
      </select>`;
  }

  get buttons() {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.inventory.showDeviceData(${this.instance})"
          data-tooltip="Network Data"
            ><span class="glyphicon glyphicon-cog"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('device', '${
            this.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
      </ul>`;
  }
};

models.link = class Link extends Base {
  static get columns() {
    return [
      { data: "name", title: "Name", search: "text" },
      { data: "description", title: "Description", search: "text" },
      { data: "subtype", title: "Subtype", search: "text" },
      { data: "model", title: "Model", search: "text" },
      { data: "location", title: "Location", search: "text" },
      { data: "vendor", title: "Vendor", search: "text" },
      { data: "source_name", title: "Source", search: "text" },
      { data: "destination_name", title: "Destination", search: "text" },
      { data: "buttons" },
    ];
  }

  static get controls() {
    return [
      super.createNewButton("link"),
      super.searchTableButton("link"),
      super.refreshTableButton("link"),
    ];
  }

  get buttons() {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 120px">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('link', '${
            this.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('link', '${this.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick="eNMS.base.showDeletionPanel(${
            this.instance
          })" data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>`;
  }
};

models.pool = class Pool extends Base {
  static get columns() {
    return [
      { data: "name", title: "Name", search: "text" },
      super.lastModifiedColumn,
      { data: "description", title: "Description", search: "text" },
      {
        data: "never_update",
        title: "Never update",
        search: "bool",
        width: "100px",
      },
      { data: "longitude", title: "Longitude", search: "text", width: "70px" },
      { data: "latitude", title: "Latitude", search: "text", width: "70px" },
      { data: "objectNumber", title: "Object Count", width: "150px" },
      { data: "buttons" },
    ];
  }

  get objectNumber() {
    return `${this.device_number} devices - ${this.link_number} links`;
  }

  static get controls() {
    return [
      super.createNewButton("pool"),
      ` <button
        class="btn btn-primary"
        onclick="eNMS.inventory.updatePools()"
        data-tooltip="Update all pools"
        type="button"
      >
        <span class="glyphicon glyphicon-flash"></span>
      </button>`,
      super.searchTableButton("pool"),
      super.refreshTableButton("pool"),
    ];
  }

  get buttons() {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 230px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.visualization.showPoolView('${this.id}')"
          data-tooltip="Internal View">
          <span class="glyphicon glyphicon-eye-open"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.inventory.showPoolObjectsPanel('${
            this.id
          }')" data-tooltip="Pool Objects"
            ><span class="glyphicon glyphicon-wrench"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.inventory.updatePools('${this.id}')"
          data-tooltip="Update"><span class="glyphicon glyphicon-refresh">
          </span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('pool', '${
            this.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('pool', '${this.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick="eNMS.base.showDeletionPanel(${
            this.instance
          })" data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>
    `;
  }
};

models.service = class Service extends Base {
  static get columns() {
    return [
      {
        data: "name",
        title: "Name",
        width: "25%",
        search: "text",
        className: "dt-body-left",
        render: function(_, __, instance) {
          return instance.type === "workflow"
            ? `<b><a href="#" onclick="eNMS.workflow.switchToWorkflow('${
                instance.id
              }')">${instance.scoped_name}</a></b>`
            : instance.scoped_name;
        },
      },
      super.lastModifiedColumn,
      { data: "type", title: "Type", search: "text" },
      { data: "vendor", title: "Vendor", search: "text" },
      { data: "operating_system", title: "Operating System", search: "text" },
      { data: "creator", title: "Creator", search: "text" },
      { data: "status", title: "Status", search: "text", width: "60px" },
      { data: "buttons" },
    ];
  }

  static get controls() {
    return [
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
      </input>
      <button
        class="btn btn-info"
        onclick="eNMS.base.openPanel({name: 'service_filtering'})"
        data-tooltip="Advanced Search"
        type="button"
      >
        <span class="glyphicon glyphicon-search"></span>
      </button>
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
    </a>
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
  </button>
    `,
    ];
  }

  get buttons() {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 270px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('results', ${
            this.instance
          })"
          data-tooltip="Results"><span class="glyphicon glyphicon-list-alt">
          </span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('logs', ${this.instance})"
          data-tooltip="Logs"><span class="glyphicon glyphicon-list"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.automation.normalRun('${this.id}')" data-tooltip="Run"
            ><span class="glyphicon glyphicon-play"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.base.showTypePanel('{self.type}', '${this.id}', 'run')"
          data-tooltip="Parameterized Run"
            ><span class="glyphicon glyphicon-play-circle"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('${this.type}', '${
      this.id
    }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.automation.exportService('${
            this.id
          }')" data-tooltip="Export"
            ><span class="glyphicon glyphicon-download"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick="eNMS.base.showDeletionPanel(${
            this.instance
          })" data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>
    `;
  }

  static postProcessing() {
    loadServiceTypes();
    $("#parent-filtering").on("change", function() {
      tables["service"].ajax.reload(null, false);
    });
  }
};

models.run = class Run extends Base {
  static get columns() {
    return [
      { data: "runtime", title: "Runtime", search: "text", width: "15%" },
      { data: "duration", title: "Duration", search: "text", width: "5%" },
      { data: "service_name", title: "Service", search: "text" },
      { data: "status", title: "Status", search: "text", width: "7%" },
      { data: "progress", title: "Progress", search: "text", width: "12%" },
      { data: "buttons", width: "130px" },
    ];
  }

  static get controls() {
    return [
      super.searchTableButton("run"),
      super.refreshTableButton("run"),
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

  get buttons() {
    return [
      `<ul class="pagination pagination-lg" style="margin: 0px; width: 100px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('logs', ${this.instance},
          '${this.runtime}')" data-tooltip="Logs">
          <span class="glyphicon glyphicon-list"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showRuntimePanel('results', ${this.instance},
          '${this.runtime}')" data-tooltip="Results">
          <span class="glyphicon glyphicon-list-alt"></span></button>
        </li>
      </ul>`,
    ];
  }
};

models.result = class Result extends Base {
  constructor(properties) {
    delete properties.result;
    super(properties);
  }

  static get columns() {
    return [
      { data: "runtime", title: "Runtime", search: "text" },
      { data: "duration", title: "Duration", search: "text" },
      { data: "device_name", title: "Device", search: "text" },
      {
        data: "success",
        title: "Success",
        render: function(_, __, instance) {
          const btn = instance.success ? "success" : "danger";
          const label = instance.success ? "Success" : "Failure";
          return `
            <button
              type="button"
              class="btn btn-${btn} btn-sm"
              style="width:100%">${label}
            </button>`;
        },
        search: "text",
        width: "80px",
      },
      { data: "buttons" },
      {
        data: "version_1",
        title: "V1",
        render: function(_, __, instance) {
          return `<input type="radio" name="v1" value="${instance.id}">`;
        },
      },
      {
        data: "version_2",
        title: "V2",
        render: function(_, __, instance) {
          return `<input type="radio" name="v2" value="${instance.id}">`;
        },
      },
    ];
  }

  static get controls() {
    return [
      `<button
        class="btn btn-info"
        onclick="eNMS.automation.compare('result')"
        data-tooltip="Compare"
        type="button"
      >
        <span class="glyphicon glyphicon-adjust"></span>
      </button>`,
    ];
  }

  get buttons() {
    return [
      `
    <ul class="pagination pagination-lg" style="margin: 0px; width: 90px">
      <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.automation.showResult('${this.id}')"
          data-tooltip="Results"><span class="glyphicon glyphicon-list-alt">
          </span></button>
      </li>
      <li>
          <button type="button" id="btn-result-${
            this.id
          }" class="btn btn-sm btn-info"
          onclick="eNMS.automation.copyClipboard('btn-result-${this.id}', ${
        this.instance
      })"
          data-tooltip="Copy to clipboard">
          <span class="glyphicon glyphicon-copy"></span></button>
      </li>
    </ul>`,
    ];
  }
};

models.task = class Task extends Base {
  static get columns() {
    return [
      { data: "name", title: "Name", search: "text" },
      { data: "service_name", title: "Service", search: "text" },
      { data: "status", title: "Status", search: "text", width: "5%" },
      {
        data: "scheduling_mode",
        title: "Scheduling",
        search: "text",
        width: "5%",
      },
      {
        data: "periodicity",
        title: "Periodicity",
        search: "text",
        render: function(_, __, instance) {
          if (instance.scheduling_mode == "standard") {
            return `${instance.frequency} ${instance.frequency_unit}`;
          } else {
            return instance.crontab_expression;
          }
        },
        width: "10%",
      },
      {
        data: "next_run_time",
        title: "Next run time",
        search: "text",
        width: "12%",
      },
      {
        data: "time_before_next_run",
        title: "Time left",
        search: "text",
        width: "12%",
      },
      { data: "buttons", width: "240px" },
    ];
  }

  static get controls() {
    return [
      super.createNewButton("task"),
      super.searchTableButton("task"),
      super.refreshTableButton("task"),
      ` <button
        class="btn btn-info"
        onclick="eNMS.automation.displayCalendar('task')"
        data-tooltip="Calendar"
        type="button"
      >
        <span class="glyphicon glyphicon-calendar"></span>
      </button>
      <button type="button" class="btn btn-success"
      onclick="eNMS.automation.schedulerAction('resume')" data-tooltip="Play"
        ><span class="glyphicon glyphicon-play"></span
      ></button>
      <button type="button" class="btn btn-danger"
      onclick="eNMS.automation.schedulerAction('pause')" data-tooltip="Pause"
        ><span class="glyphicon glyphicon-pause"></span
      ></button>`,
    ];
  }

  get buttons() {
    const state = this.is_active
      ? ["disabled", "active"]
      : ["active", "disabled"];
    return [
      `<ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('task', '${
            this.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('task', '${this.id}', 'duplicate')"
          data-tooltip="Duplicate">
          <span class="glyphicon glyphicon-duplicate"></span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success ${state[0]}" ${
        state[0]
      }
          onclick="eNMS.automation.resumeTask('${this.id}')" data-tooltip="Play"
            ><span class="glyphicon glyphicon-play"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger ${state[1]}" ${
        state[1]
      }
          onclick="eNMS.automation.pauseTask('${this.id}')" data-tooltip="Pause"
            ><span class="glyphicon glyphicon-pause"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick="eNMS.base.showDeletionPanel(${
            this.instance
          })" data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>`,
    ];
  }
};

models.user = class User extends Base {
  static get columns() {
    return [
      { data: "name", title: "Username", search: "text" },
      { data: "email", title: "Email Address", search: "text" },
      { data: "buttons", width: "130px" },
    ];
  }

  static get controls() {
    return [
      super.createNewButton("user"),
      super.searchTableButton("user"),
      super.refreshTableButton("user"),
    ];
  }

  get buttons() {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('user', '${
            this.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('user', '${this.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick="eNMS.base.showDeletionPanel(${
            this.instance
          })" data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>`,
    ];
  }
};

models.server = class Server extends Base {
  static get columns() {
    return [
      { data: "name", title: "Username", search: "text" },
      { data: "description", title: "Description", search: "text" },
      { data: "ip_address", title: "IP address", search: "text" },
      { data: "weight", title: "Weight", search: "text" },
      { data: "status", title: "Status", search: "text" },
      { data: "buttons", width: "120px" },
    ];
  }

  static get controls() {
    return [
      super.createNewButton("server"),
      super.searchTableButton("server"),
      super.refreshTableButton("server"),
    ];
  }

  get buttons() {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('server', '${
            this.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('server', '${this.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick="eNMS.base.showDeletionPanel(${
            this.instance
          })" data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>`,
    ];
  }
};

models.changelog = class Changelog extends Base {
  static get columns() {
    return [
      { data: "time", title: "Time", search: "text", width: "200px" },
      { data: "user", title: "User", search: "text", width: "100px" },
      { data: "severity", title: "Severity", search: "text", width: "80px" },
      {
        data: "content",
        title: "Content",
        search: "text",
        className: "dt-body-left",
      },
    ];
  }

  static get controls() {
    return [
      super.createNewButton("changelog"),
      super.searchTableButton("changelog"),
      super.refreshTableButton("changelog"),
    ];
  }
};

models.session = class Session extends Base {
  static get columns() {
    return [
      { data: "timestamp", title: "Timestamp", search: "text", width: "200px" },
      { data: "device_name", title: "Device", search: "text", width: "150px" },
      { data: "user", title: "User", search: "text", width: "100px" },
      { data: "name", title: "Session UUID", search: "text", width: "300px" },
      { data: "buttons", width: "40px" },
    ];
  }

  static get controls() {
    return [
      super.searchTableButton("session"),
      super.refreshTableButton("session"),
    ];
  }

  get buttons() {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px;">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="eNMS.inventory.showSessionLog(${
            this.id
          })" data-tooltip="Session Log"
            ><span class="glyphicon glyphicon-list"></span
          ></button>
        </li>
      </ul>`,
    ];
  }
};

models.event = class Event extends Base {
  static get columns() {
    return [
      { data: "name", title: "Name", search: "text" },
      { data: "service_name", title: "Service", search: "text" },
      { data: "log_source", title: "Log", search: "text" },
      { data: "log_content", title: "Content", search: "text" },
      { data: "buttons", width: "120px" },
    ];
  }

  static get controls() {
    return [
      super.createNewButton("event"),
      super.searchTableButton("event"),
      super.refreshTableButton("event"),
    ];
  }

  get buttons() {
    return [
      `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 150px">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('event', '{self.id}')"
          data-tooltip="Edit"><span class="glyphicon glyphicon-edit">
          </span></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.base.showTypePanel('event', '{self.id}', 'duplicate')"
          data-tooltip="Duplicate">
          <span class="glyphicon glyphicon-duplicate"></span></button>
        </li>
        ${this.deleteInstanceButton}
      </ul>
    `,
    ];
  }
};

configureNamespace("table", [
  filterTable,
  refreshTable,
  refreshTablePeriodically,
]);
