/*
global
action: true
automation: false
CodeMirror: false
Dropzone: false
formProperties: true
JSONEditor: false
jsPanel: false
page: false
*/

import {
  call,
  configureForm,
  configureNamespace,
  downloadFile,
  initCodeMirror,
  notify,
  observeMutations,
  openPanel,
  serializeForm,
  showInstancePanel,
} from "./base.js";
import { currentPath, drawTree } from "./builder.js";
import { network } from "./networkBuilder.js";
import { refreshTable, tableInstances, tables } from "./table.js";
import {
  currentRuntime,
  getServiceState,
  getWorkflowState,
  switchToWorkflow,
  updateRuntimeVariable,
  workflow,
} from "./workflowBuilder.js";

export let runtimeDisplay = localStorage.getItem("userFiltering-run") || "users";

function openServicePanel(tableId, bulkMode) {
  const args = tableId ? [null, bulkMode, tableId] : [];
  const panelType =
    bulkMode == "bulk-filter" ? "service" : $("#service-type-dd-list").val();
  showInstancePanel(panelType, ...args);
}

function buildLinks(result, id) {
  const base = `get_result("${result.service_name}"`;
  const link = result.device_name ? `${base}, device=device.name)` : `${base})`;
  return `
    <div class="modal-body">
      <div class="input-group" style="width: 500px">
        <input id="link-${id}" type="text" class="form-control" value='${link}'>
        <span class="input-group-btn">
          <button class="btn btn-default"
            onclick="eNMS.base.copyToClipboard({text: 'link-${id}', isId: true})"
            type="button"
          >
            <span class="glyphicon glyphicon-copy"></span>
          </button>
        </span>
      </div>
    </div>`;
}

function copyClipboard(elementId, result) {
  const target = document.getElementById(elementId);
  if (!$(`#tooltip-${elementId}`).length) {
    jsPanel.tooltip.create({
      id: `tooltip-${elementId}`,
      content: buildLinks(result, elementId),
      contentSize: "auto",
      connector: true,
      delay: 0,
      header: false,
      mode: "sticky",
      position: {
        my: "right-top",
        at: "left-bottom",
      },
      target: target,
      ttipEvent: "click",
      theme: "light",
    });
  }
  target.click();
}

function downloadRun(type, serviceId) {
  const cmInstance = $(`#service-${type}-${serviceId}`).data("CodeMirrorInstance");
  const content = cmInstance
    ? cmInstance.getValue()
    : $(`#service-${type}-${serviceId}`).html();
  const extension = cmInstance ? "txt" : "html";
  downloadFile(`${type}-${serviceId}`, content, extension);
}

export function flipRuntimeDisplay(display) {
  runtimeDisplay = display || (runtimeDisplay == "users" ? "user" : "users");
  localStorage.setItem("userFiltering-run", runtimeDisplay);
  $("#user-filtering-icon-run").attr("class", `fa fa-${runtimeDisplay}`);
  if (!display) switchToWorkflow(currentPath);
}

function stopRun(runtime) {
  call({
    url: `/stop_run/${runtime}`,
    callback: () => {
      notify("Stopping service...", "success", 5);
    },
  });
}

function showResult(id) {
  openPanel({
    name: "result",
    content: `
      <div class="input-group" style="width:100%">
        <input
          id="result-path-${id}"
          type="text"
          class="form-control"
          style="height: 34px"
          value="results"
        >
        <span class="input-group-btn">
          <button class="btn btn-default pull-right"
            onclick="eNMS.base.copyToClipboard({text: 'result-path-${id}', isId: true})"
            type="button"
            title="Copy path to variable in result dictionary to clipboard"
          >
            <span class="glyphicon glyphicon-copy"></span>
          </button>
        </span>
        <span class="input-group-btn">
          <button
            id="download-result-${id}"
            class="btn btn-default pull-right"
            type="button"
            style="height: 34px; width: 40px"
          >
            <span
              class="glyphicon glyphicon-center glyphicon-download"
              aria-hidden="true"
            ></span>
          </button>
        </span>
      </div>
      <div id="content-${id}" style="height:95%"></div>`,
    title: "Result",
    id: id,
    callback: function() {
      call({
        url: `/get_result/${id}`,
        callback: (result) => {
          const jsonResult = result;
          $(`#download-result-${id}`).on("click", function() {
            downloadFile(`result-${id}`, JSON.stringify(result), "json");
          });
          const options = {
            mode: "view",
            modes: ["code", "view"],
            onModeChange: function(newMode) {
              editor.set(newMode == "code" ? result : jsonResult);
              document.querySelectorAll(".jsoneditor-string").forEach((el) => {
                el.innerText = el.innerText.replace(/(?:\\n)/g, "\n");
              });
            },
            onEvent(node, event) {
              if (event.type === "click") {
                let path = node.path.map((key) =>
                  typeof key == "string" ? `"${key}"` : key
                );
                $(`#result-path-${id}`).val(`results[${path.join("][")}]`);
              }
            },
          };
          const content = document.getElementById(`content-${id}`);
          observeMutations(content, ".jsoneditor-string", function(element) {
            if (!element.mutated) {
              element.innerText = element.innerText
                .replace(/ /g, "\u00a0")
                .replace(/(?:\\n)/g, "\n");
              element.mutated = true;
            }
          });
          let editor = new JSONEditor(content, options, jsonResult);
        },
      });
    },
  });
}

export const showRuntimePanel = function(
  type,
  service,
  runtime,
  table,
  newRuntime,
  fullResult
) {
  if (runtime?.startsWith("#runtimes")) runtime = $(runtime).val();
  if (!runtime) runtime = currentRuntime;
  const displayFunction =
    type == "logs"
      ? displayLogs
      : type == "report"
      ? displayReport
      : service.type == "workflow" && !table
      ? displayResultsTree
      : displayResultsTable;
  const panelType =
    type == "logs"
      ? "logs"
      : type == "report"
      ? "report"
      : service.type == "workflow" && !table
      ? "tree"
      : "table";
  const panelId = `${panelType}-${service.id}`;
  call({
    url: `/get_runtimes/${service.id}`,
    data: { display: runtimeDisplay },
    callback: (runtimes) => {
      if (newRuntime) runtimes.push([runtime, runtime]);
      if (!runtimes.length) return notify(`No ${type} yet.`, "error", 5);
      let content;
      let header;
      const headerColor = panelType == "logs" ? "282828" : "fafafa";
      let headerStyle = `background-color: #${headerColor};`;
      if (panelType == "logs" || panelType == "report") {
        const autoscrollBox =
          panelType == "logs"
            ? `
          <div style="float: left;">
            <input
              type="checkbox"
              class="form-control-bool"
              id="autoscroll-checkbox-${panelId}"
              style="cursor: pointer;"
              title="Scroll to bottom automatically when refreshing"
            checked>
            <label
              style="margin-left: 8px;
              font-size: 20px;
              color: white;"
            >Auto-scroll</label>
          </div>`
            : "";
        const searchButton = 
          panelType == "logs"
          ? `
            <div style="width: 30px; float: left; margin-left: 15px;">
              <button
                id="search-button-${panelId}"
                class="btn btn-default pull-right"
                data-tooltip="Search"
                type="button"
              >
                <span
                  class="glyphicon glyphicon-search"
                  aria-hidden="true"
                ></span>
              </button>
            </div>`
          : "";
        header = `
        <div class="modal-body centered" >
          <nav
            id="controls"
            class="navbar navbar-default nav-controls"
            role="navigation"
          >
            <div style="width: 380px; float: left;">
              <select
                id="runtimes-${panelId}"
                name="runtimes"
                class="form-control"
                data-live-search="true"
              ></select>
            </div>
            <div style="width: 30px; float: left; margin-left: 15px;">
              <button
                class="btn btn-default pull-right"
                onclick="eNMS.automation.downloadRun('${panelType}', ${service.id})"
                data-tooltip="Download"
                type="button"
              >
                <span
                  class="glyphicon glyphicon-download"
                  aria-hidden="true"
                ></span>
              </button>
            </div>
            ${searchButton}
            ${autoscrollBox}
          </nav>
          <div id="search-logs-${panelId}" style="display: none">
            <input
              type="text"
              id="search-field-${panelId}"
              class="form-control"
              placeholder="&#xF002; Search"
              style="font-family: Arial, FontAwesome;"
            >
          </div>
        </div>`;
        content = `<div class="modal-body"><div id="service-${panelId}"></div></div>`;
      } else if (panelType == "tree") {
        const serviceProperties = { id: service.id, name: service.name };
        content = `
        <div class="modal-body">
          <div style="width: 900px; float: left;">
            <select
              id="runtimes-${panelId}"
              name="runtimes"
              class="form-control"
              data-live-search="true"
            ></select>
          </div>
          <div style="width: 30px; float: left; margin-left: 15px;">
            <button
              class="btn btn-info pull-right"
              onclick="eNMS.automation.showRuntimePanel(
                'results', ${JSON.stringify(serviceProperties).replace(/"/g, "'")},
                '#runtimes-${panelId}', 'full_result', null, true)"
              data-tooltip="All Results"
              type="button"
            >
              <span
                class="glyphicon glyphicon-list-alt"
                aria-hidden="true"
              ></span>
            </button>
          </div>
          <hr>
          <div id="result-${panelId}" style="height: 500px; margin-top: 30px"></div>
        </div>`;
      } else {
        if (!table) table = "result";
        content = `
        <div class="modal-body">
          <div id="tooltip-overlay" class="overlay"></div>
          <form
            id="search-form-${table}-${service.id}"
            class="form-horizontal form-label-left"
            method="post"
          >
            <nav
              id="controls-${table}-${service.id}"
              class="navbar navbar-default nav-controls"
              role="navigation"
            >
              <button
                style="background:transparent; border:none; 
                color:transparent; width: 300px;"
                type="button"
              >
                <select
                  id="runtimes-${panelId}"
                  name="runtimes"
                  class="form-control"
                ></select>
              </button>
            </nav>
            <table
              id="table-${table}-${service.id}"
              class="table table-striped table-bordered table-hover"
              cellspacing="0"
              width="100%"
            ></table>
          </form>
        </div>`;
      }
      openPanel({
        name: panelType,
        headerToolbar: header,
        headerStyle: headerStyle,
        content: content,
        size: "1200 650",
        type: "result",
        title: `${type} - ${service.name}`,
        id: service.id,
        tableId: panelType == "table" ? `result-${service.id}` : null,
        callback: function() {
          $(`#runtimes-${panelId}`).empty();
          runtimes.forEach((runtime) => {
            $(`#runtimes-${panelId}`).append(
              $("<option></option>")
                .attr("value", runtime[0])
                .text(runtime[1])
            );
          });
          if (!runtime || ["normal", "latest"].includes(runtime)) {
            runtime = runtimes[0][0];
          }
          $(`#runtimes-${panelId}`)
            .val(runtime)
            .selectpicker("refresh");
          $(`#runtimes-${panelId}`).on("change", function() {
            displayFunction(service, this.value, true, table, true, fullResult);
          });
          displayFunction(service, runtime, null, table, false, fullResult);
        },
      });
    },
  });
};

function displayReport(service, runtime, change) {
  let editor;
  const id = `service-report-${service.id}`;
  if (service.report_format == "text") {
    if (change) {
      editor = $(`#${id}`).data("CodeMirrorInstance");
      editor.setValue("");
    } else {
      editor = initCodeMirror(id, "logs");
    }
  }
  call({
    url: `/get_report/${service.id}/${runtime}`,
    callback: function(report) {
      if (service.report_format == "text") {
        editor.setValue(report);
        editor.refresh();
      } else {
        $(`#${id}`).html(report);
      }
    },
  });
}

function displayLogs(service, runtime, change) {
  let editor;
  if (change) {
    editor = $(`#service-logs-${service.id}`).data("CodeMirrorInstance");
    editor.setValue("");
  } else {
    editor = initCodeMirror(`service-logs-${service.id}`, "logs");
  }
  let timer = false;
  $(`#search-button-logs-${service.id}`).on("click", function() {
    $(`#search-logs-logs-${service.id}`)
      .toggle()
      .find("input")
      .focus();
  });
  $(`#search-field-logs-${service.id}`).on("input", function() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(function() {
      const currentRuntime = $(`#runtimes-logs-${service.id}`).val();
      refreshLogs(service, currentRuntime, editor, true, false, 0, true);
    }, 500);
  });
  $(`#runtimes-logs-${service.id}`).on("change", function() {
    refreshLogs(service, this.value, editor, true);
  });
  refreshLogs(service, runtime, editor, true);
}

export function displayResultsTree(service, runtime) {
  const path =
    currentPath && currentPath.endsWith(service.id) ? currentPath : service.id;
  call({
    url: `/get_instance_tree/workflow/${path}/${runtime}`,
    callback: function(data) {
      if (!data) return notify("No results to display.", "error", 5);
      drawTree(service.id, data.tree, true);
    },
  });
}

function displayResultsTable(service, runtime, _, type, refresh, fullResult) {
  // eslint-disable-next-line new-cap
  type = type ?? "result";
  if (refresh) {
    tableInstances[`result-${service.id}`].constraints.parent_runtime = runtime;
    refreshTable(`result-${service.id}`);
  } else {
    let constraints = { parent_runtime: runtime || currentRuntime };
    if (!fullResult) {
      Object.assign(constraints, {
        service_id: service.id,
        service_id_filter: "equality",
      });
    }
    if ($("#device-filter").val()) {
      Object.assign(constraints, {
        device_id: $("#device-filter").val(),
        device_id_filter: "equality",
      });
    }
    new tables[type](service.id, constraints);
  }
}

function refreshLogs(service, runtime, editor, first, wasRefreshed, line, search) {
  if (!$(`#service-logs-${service.id}`).length) return;
  if (runtime != $(`#runtimes-logs-${service.id}`).val()) return;
  const windowSize = automation.workflow.logs_rolling_window;
  call({
    url: `/get_service_logs/${service.id}/${runtime}`,
    data: {
      line: line || 0,
      device: $("#device-filter").val(),
      search: $(`#search-field-logs-${service.id}`).val(),
    },
    callback: function(result) {
      if (search) editor.setValue("");
      if (!first && result.refresh && result.logs.length) {
        // eslint-disable-next-line new-cap
        editor.replaceRange(result.logs, CodeMirror.Pos(editor.lineCount()));
        if ($(`#autoscroll-checkbox-logs-${service.id}`).prop("checked")) {
          editor.setCursor(editor.lineCount(), 0);
        }
        if (
          $(`#rolling-window-checkbox-logs-${service.id}`).prop("checked")
          && editor.lineCount() > windowSize
        ) {
          const cutoffPosition = CodeMirror.Pos(editor.lineCount() - windowSize, 0);
          editor.replaceRange("", CodeMirror.Pos(0, 0), cutoffPosition);
          editor.setOption("firstLineNumber", Math.max(1, line - windowSize));
        }
      } else if (first || !result.refresh) {
        editor.setValue(`Gathering logs for '${service.name}'...${result.logs}`);
        editor.refresh();
      }
      if (search) return;
      if (first || result.refresh) {
        setTimeout(
          () =>
            refreshLogs(service, runtime, editor, false, result.refresh, result.line),
          automation.workflow.logs_refresh_rate
        );
      } else if (wasRefreshed) {
        setTimeout(() => {
          $(`#logs-${service.id}`).remove();
          const table = service.type == "workflow" ? null : "result";
          const panel = service.display_report ? "report" : "results";
          if (page == "workflow_builder") getWorkflowState();
          showRuntimePanel(panel, service, runtime, table);
        }, 1000);
      }
    },
  });
}

function submitInitialForm(serviceId) {
  call({
    url: `/run_service/${serviceId}`,
    form: `initial-${serviceId}-form-${serviceId}`,
    callback: (result) => {
      if (result.error) {
        notify(result.error, "error", 5);
      } else {
        runLogic(result);
        $(`#parameterized_form-${serviceId}`).remove();
      }
    },
  });
}

export const runService = function({ id, path, type, parametrization }) {
  if (parametrization) {
    openPanel({
      name: "parameterized_form",
      id: id,
      url: `/parameterized_form/${id}`,
      title: "Parameterized Form",
      size: "1100px auto",
      checkRbac: false,
      callback: function() {
        call({
          url: `/get_form_properties/${id}`,
          callback: function(properties) {
            formProperties[`initial-${id}`] = properties;
            configureForm(`initial-${id}`, id);
            $(`#parameterized_form-${id} script`).each((_, s) => eval(s.innerHTML));
          },
        });
      },
    });
  } else {
    call({
      url: `/run_service/${path || id}`,
      form: type ? `${type}-form-${id}` : null,
      callback: function(result) {
        if (type) $(`#${type}-${id}`).remove();
        runLogic(result);
      },
    });
  }
};

export function runLogic(result) {
  if (result.error) return notify(result.error, "error", 5, true);
  const service = result.restart
    ? result.service
    : result.service.superworkflow || result.service;
  showRuntimePanel("logs", service, result.runtime, undefined, true);
  notify(`Service '${service.name}' started.`, "success", 5, true);
  if (page == "workflow_builder" && workflow) {
    if (service != result.service) {
      switchToWorkflow(service.id, null, result.runtime);
    } else if (result.service.id != workflow.id) {
      getServiceState(result.service.id, true);
    } else {
      const option = `<option value='${result.runtime}'>${result.runtime}</option>`;
      updateRuntimeVariable(result.runtime);
      $("#current-runtime")
        .append(option)
        .val(result.runtime)
        .selectpicker("refresh");
    }
  } else if (page == "network_builder") {
    network.runtime = result.runtime;
  }
  $(`#${result.service.type}-${result.service.id}`).remove();
}

function pauseTask(id) {
  call({
    url: `/task_action/pause/${id}`,
    callback: function() {
      $(`#pause-resume-${id}`)
        .attr("onclick", `eNMS.automation.resumeTask('${id}')`)
        .text("Resume");
      refreshTable("task");
      notify("Task paused.", "success", 5);
    },
  });
}

function resumeTask(id) {
  call({
    url: `/task_action/resume/${id}`,
    callback: function() {
      $(`#pause-resume-${id}`)
        .attr("onclick", `eNMS.automation.pauseTask('${id}')`)
        .text("Pause");
      refreshTable("task");
      notify("Task resumed.", "success", 5);
    },
  });
}

export function field(name, type, id) {
  const fieldId = id ? `${type}-${name}-${id}` : `${type}-${name}`;
  return $(`#${fieldId}`);
}

function displayCalendar(calendarType) {
  openPanel({
    name: "calendar",
    title: `Calendar - ${calendarType}`,
    id: calendarType,
    content: `
      <div class="modal-body">
        <div id="calendar" style="height: 500px"></div>
      </div>`,
    callback: () => {
      call({
        url: `/calendar_init/${calendarType}`,
        callback: function(tasks) {
          let events = [];
          for (const [name, properties] of Object.entries(tasks)) {
            events.push({
              title: name,
              id: properties.id,
              description: properties.description,
              start: new Date(...properties.start),
              runtime: properties.runtime,
              service: properties.service_properties,
            });
          }
          $("#calendar").fullCalendar({
            height: 600,
            header: {
              left: "prev,next today",
              center: "title",
              right: "month,agendaWeek,agendaDay,listMonth",
            },
            selectable: true,
            selectHelper: true,
            eventClick: function(e) {
              if (calendarType == "task") {
                showInstancePanel("task", e.id);
              } else {
                showRuntimePanel("results", e.service, e.runtime, "result");
              }
            },
            editable: true,
            events: events,
          });
        },
      });
    },
  });
}

function schedulerAction(action) {
  call({
    url: `/scheduler_action/${action}`,
    form: "search-form-task",
    callback: function() {
      refreshTable("task");
      notify(`All tasks have been ${action}d.`, "success", 5, true);
    },
  });
}

Object.assign(action, {
  Edit: (service) => showInstancePanel(service.type, service.id),
  Duplicate: (service) => showInstancePanel(service.type, service.id, "duplicate"),
  Run: (service) => runService({ id: service.id, form: service.parameterized_form }),
  "Parameterized Run": (service) =>
    runService({ id: service.id, parametrization: true }),
  Logs: (service) => showRuntimePanel("logs", service, currentRuntime),
  Reports: (service) => showRuntimePanel("report", service, currentRuntime),
  Results: (service) => showRuntimePanel("results", service, currentRuntime, "result"),
});

export function showRunServicePanel({ instance, tableId, targets, type }) {
  if (targets && !targets.length) {
    return notify("No targets has been selected", "error", 5);
  }
  const table = tableInstances?.[tableId];
  const targetType = type || instance.type;
  const title = type
    ? `all ${type}s`
    : tableId
    ? `all ${type}s in table`
    : `${instance.type} '${instance.name}'`;
  const panelId = tableId || instance?.id || type;
  openPanel({
    name: "run_service",
    title: `Run service on ${title}`,
    size: "900px 300px",
    id: panelId,
    callback: function() {
      $(`#run_service-type-${panelId}`).val(targetType);
      if (type && !targets) {
        let form = serializeForm(`#search-form-${panelId}`, `${type}_filtering`);
        if (table) form = { ...form, ...table.constraints };
        call({
          url: `/filtering/${type}`,
          data: { form: form, bulk: "id" },
          callback: function(instances) {
            $(`#run_service-targets-${panelId}`).val(instances.join("-"));
          },
        });
      } else if (targets) {
        $(`#run_service-targets-${panelId}`).val(targets.join("-"));
      } else {
        $(`#run_service-targets-${panelId}`).val(instance.id);
      }
    },
  });
}

function runServicesOnTargets(id) {
  call({
    url: "/run_service_on_targets",
    form: `run_service-form-${id}`,
    callback: function(result) {
      runLogic(result);
      $(`#run_service-${id}`).remove();
    },
  });
}

configureNamespace("automation", [
  copyClipboard,
  displayCalendar,
  downloadRun,
  field,
  flipRuntimeDisplay,
  openServicePanel,
  pauseTask,
  resumeTask,
  runService,
  runServicesOnTargets,
  schedulerAction,
  showResult,
  showRunServicePanel,
  showRuntimePanel,
  stopRun,
  submitInitialForm,
]);
