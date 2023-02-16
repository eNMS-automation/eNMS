/*
global
action: true
automation: false
CodeMirror: false
Diff2HtmlUI: false
Dropzone: false
formProperties: true
JSONEditor: false
jsPanel: false
page: false
*/

import {
  call,
  cantorPairing,
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
import { currentPath } from "./builder.js";
import { network } from "./networkBuilder.js";
import { refreshTable, tableInstances, tables } from "./table.js";
import {
  currentRuntime,
  getServiceState,
  switchToWorkflow,
  workflow,
} from "./workflowBuilder.js";

function openServicePanel(tableId) {
  const args = tableId ? [null, "bulk", tableId] : [];
  showInstancePanel($("#service-type-list").val(), ...args);
}

export function displayDiff(type, instanceId) {
  const objectType = type.includes("result") ? "result" : type;
  const v1 = $(`input[name=v1-${type}-${instanceId}]:checked`).val();
  const v2 = $(`input[name=v2-${type}-${instanceId}]:checked`).val();
  if (!v1 || !v2) {
    notify("Select two versions to compare first.", "error", 5);
  } else if (v1 == v2) {
    notify("You must select two distinct versions.", "error", 5);
  } else {
    const cantorId = cantorPairing(parseInt(v1), parseInt(v2));
    openPanel({
      name: "compare",
      title: `Compare ${objectType}`,
      id: cantorId,
      size: "700 500",
      content: `
        <nav
          class="navbar navbar-default nav-controls"
          role="navigation"
          style="margin-top: 30px"
        >
          <input
            id="diff-type-${cantorId}"
            type="checkbox"
            data-onstyle="info"
            data-offstyle="primary"
          >
          <input
            name="diff-context-lines"
            id="slider-${cantorId}"
            class="slider"
          >
        </nav>
        <div class="modal-body">
          <div id="content-${cantorId}" style="height:100%"></div>
        </div>`,
      callback: () => {
        $(`#diff-type-${cantorId}`).bootstrapToggle({
          on: "Side by side",
          off: "Line by line",
          width: "120px",
        });
        const valueToLabel = { 0: 1, 1: 3, 2: 10, 3: 100, 4: "All" };
        $(`#slider-${cantorId}`)
          .bootstrapSlider({
            value: 1,
            ticks: [...Array(5).keys()],
            ticks_labels: Object.values(valueToLabel),
            formatter: (value) => `Lines of context: ${valueToLabel[value]}`,
            tooltip: "always",
          })
          .change(function () {
            let value = valueToLabel[this.value];
            if (value == "All") value = 999999;
            call({
              url: `/compare/${objectType}/${instanceId}/${v1}/${v2}/${value}`,
              callback: (result) => {
                let diff2htmlUi = new Diff2HtmlUI({ diff: result });
                $(`#diff-type-${cantorId}`)
                  .on("change", function () {
                    diff2htmlUi.draw(`#content-${cantorId}`, {
                      matching: "lines",
                      drawFileList: true,
                      outputFormat: $(this).prop("checked")
                        ? "side-by-side"
                        : "line-by-line",
                    });
                    $(".d2h-tag").hide();
                  })
                  .change();
              },
            });
          })
          .trigger("change");
      },
    });
  }
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
  const extension = cmInstance ? "txt" : "html"
  downloadFile(`${type}-${serviceId}`, content, extension);
}

function stopRun(runtime) {
  call({
    url: `/stop_run/${runtime}`,
    callback: (result) => {
      if (!result) {
        notify("The service is not currently running.", "error", 5);
      } else {
        notify("Stopping service...", "success", 5);
      }
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
    callback: function () {
      call({
        url: `/get_result/${id}`,
        callback: (result) => {
          const jsonResult = result;
          $(`#download-result-${id}`).on("click", function () {
            downloadFile(`result-${id}`, JSON.stringify(result), "json");
          });
          const options = {
            mode: "view",
            modes: ["code", "view"],
            onModeChange: function (newMode) {
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
          observeMutations(content, ".jsoneditor-string", function (element) {
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

export const showRuntimePanel = function (
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
    callback: (runtimes) => {
      if (newRuntime) runtimes.push([runtime, runtime]);
      if (!runtimes.length) return notify(`No ${type} yet.`, "error", 5);
      let content;
      if (panelType == "logs" || panelType == "report") {
        content = `
        <div class="modal-body">
          <nav
            id="controls"
            class="navbar navbar-default nav-controls"
            role="navigation"
          >
            <div style="width: 280px; float: left;">
              <select
                id="runtimes-${panelId}"
                name="runtimes"
                class="form-control"
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
          </nav>
          <hr>
          <div id="service-${panelId}"></div>
        </div>
        `;
      } else if (panelType == "tree") {
        const serviceProperties = { id: service.id, name: service.name };
        content = `
        <div class="modal-body">
          <div style="width: 900px; float: left;">
            <select
              id="runtimes-${panelId}"
              name="runtimes"
              class="form-control"
            ></select>
          </div>
          <div style="width: 30px; float: left; margin-left: 15px;">
            <button
              class="btn btn-info pull-right"
              onclick="eNMS.automation.showRuntimePanel(
                'results', ${JSON.stringify(serviceProperties).replace(/"/g, "'")},
                '#runtimes-${panelId}', 'result', null, true)"
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
        content: content,
        size: "1000 600",
        type: "result",
        title: `${type} - ${service.name}`,
        id: service.id,
        tableId: panelType == "table" ? `result-${service.id}` : null,
        callback: function () {
          $(`#runtimes-${panelId}`).empty();
          runtimes.forEach((runtime) => {
            $(`#runtimes-${panelId}`).append(
              $("<option></option>").attr("value", runtime[0]).text(runtime[1])
            );
          });
          if (!runtime || ["normal", "latest"].includes(runtime)) {
            runtime = runtimes[0][0];
          }
          $(`#runtimes-${panelId}`).val(runtime).selectpicker("refresh");
          $(`#runtimes-${panelId}`).on("change", function () {
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
    callback: function (report) {
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
  $(`#runtimes-logs-${service.id}`).on("change", function () {
    refreshLogs(service, this.value, editor, true);
  });
  refreshLogs(service, runtime, editor, true);
}

function displayResultsTree(service, runtime) {
  call({
    url: `/get_workflow_results/${currentPath || service.id}/${runtime}`,
    callback: function (data) {
      $(`#result-tree-${service.id}`).jstree("destroy").empty();
      if (!data) return notify("No results to display.", "error", 5);
      let tree = $(`#result-tree-${service.id}`).jstree({
        core: {
          animation: 100,
          themes: { stripes: true },
          data: data,
        },
        plugins: ["html_row", "types", "wholerow"],
        types: {
          default: {
            icon: "glyphicon glyphicon-file",
          },
          workflow: {
            icon: "fa fa-sitemap",
          },
        },
        html_row: {
          default: function (el, node) {
            if (!node) return;
            const data = JSON.stringify(node.data.properties);
            let progressSummary;
            if (node.data.progress) {
              progressSummary = `
                <div style="position: absolute; top: 0px; right: 160px">
                  <span style="color: #32cd32">
                    ${node.data.progress.success || 0} passed
                  </span>
                  ${
                    node.data.progress.skipped > 0
                      ? `<span style="color: #000000">-</span>
                    <span style="color: #7D7D7D">
                    ${node.data.progress.skipped || 0} skipped
                    </span>
                  `
                      : ""
                  }
                  <span style="color: #000000">-</span>
                  <span style="color: #FF6666">
                    ${node.data.progress.failure || 0} failed
                  </span>
                </div>
              `;
            } else {
              progressSummary = "";
            }
            $(el).find("a").first().append(`
              ${progressSummary}
              <div style="position: absolute; top: 0px; right: 50px">
                <button type="button"
                  class="btn btn-xs btn-primary"
                  onclick='eNMS.automation.showRuntimePanel(
                    "logs", ${data}, "${runtime}"
                  )'><span class="glyphicon glyphicon-list"></span>
                </button>
                <button type="button"
                  class="btn btn-xs btn-primary"
                  onclick='eNMS.automation.showRuntimePanel(
                    "report", ${data}, "${runtime}"
                  )'><span class="glyphicon glyphicon-modal-window"></span>
                </button>
                <button type="button"
                  class="btn btn-xs btn-primary"
                  onclick='eNMS.automation.showRuntimePanel(
                    "results", ${data}, "${runtime}", "result"
                  )'>
                  <span class="glyphicon glyphicon-list-alt"></span>
                </button>
              </div>
            `);
          },
        },
      });
      tree.bind("loaded.jstree", function () {
        tree.jstree("open_all");
      });
      tree.unbind("dblclick.jstree").bind("dblclick.jstree", function (event) {
        const service = tree.jstree().get_node(event.target);
        showRuntimePanel("results", service.data.properties, runtime, "result");
      });
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
    new tables[type](service.id, constraints);
  }
}

function refreshLogs(service, runtime, editor, first, wasRefreshed, line) {
  if (!$(`#service-logs-${service.id}`).length) return;
  if (runtime != $(`#runtimes-logs-${service.id}`).val()) return;
  call({
    url: `/get_service_logs/${service.id}/${runtime}`,
    data: { line: line || 0, device: $("#device-filter").val() },
    callback: function (result) {
      if (!first && result.refresh && result.logs.length) {
        // eslint-disable-next-line new-cap
        editor.replaceRange(`\n${result.logs}`, CodeMirror.Pos(editor.lineCount()));
        editor.setCursor(editor.lineCount(), 0);
      } else if (first || !result.refresh) {
        editor.setValue(`Gathering logs for '${service.name}'...\n\n${result.logs}`);
        editor.refresh();
      }
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

export const runService = function ({ id, path, type, parametrization }) {
  if (parametrization) {
    openPanel({
      name: "parameterized_form",
      id: id,
      url: `/parameterized_form/${id}`,
      title: "Parameterized Form",
      size: "900px auto",
      checkRbac: false,
      callback: function () {
        call({
          url: `/get_form_properties/${id}`,
          callback: function (properties) {
            formProperties[`initial-${id}`] = properties;
            configureForm(`initial-${id}`, id);
          },
        });
      },
    });
  } else {
    call({
      url: `/run_service/${path || id}`,
      form: type ? `${type}-form-${id}` : null,
      callback: function (result) {
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
      $("#current-runtime").append(option).val(result.runtime).selectpicker("refresh");
    }
  } else if (page == "network_builder") {
    network.runtime = result.runtime;
  }
  $(`#${result.service.type}-${result.service.id}`).remove();
}

export function exportServices(tableId) {
  call({
    url: `/export_services`,
    form: `search-form-${tableId}`,
    callback: () => {
      notify("Services successfully exported.", "success", 5, true);
    },
  });
}

function pauseTask(id) {
  call({
    url: `/task_action/pause/${id}`,
    callback: function () {
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
    callback: function () {
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
        callback: function (tasks) {
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
            eventClick: function (e) {
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
    callback: function () {
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
    callback: function () {
      $(`#run_service-type-${panelId}`).val(targetType);
      if (type && !targets) {
        let form = serializeForm(`#search-form-${panelId}`, `${type}_filtering`);
        if (table) form = { ...form, ...table.constraints };
        call({
          url: `/filtering/${type}`,
          data: { form: form, bulk: "id" },
          callback: function (instances) {
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
    callback: function (result) {
      runLogic(result);
      $(`#run_service-${id}`).remove();
    },
  });
}

function showImportServicesPanel() {
  openPanel({
    name: "import_services",
    title: "Import Services",
    size: "600 500",
    callback: () => {
      new Dropzone(document.getElementById(`dropzone-services`), {
        url: "/import_services",
        timeout: automation.service_import.timeout,
        init: function () {
          this.on("sending", function (file, xhr) {
            xhr.ontimeout = function () {
              notify(`Upload of File "${file.name}" timed out.`, "error", 5, true);
              file.previewElement.classList.add("dz-error");
            };
          });
        },
        error: function (file, message) {
          const error = typeof message == "string" ? message : message.alert;
          const log = `File ${file.name} was not uploaded - ${error}`;
          notify(log, "error", 5, true);
          file.previewElement.classList.add("dz-error");
        },
        success: function (file, message) {
          const log = `File ${file.name} uploaded with response "${message}"`;
          notify(log, "success", 5, true);
          file.previewElement.classList.add("dz-success");
        },
        accept: function (file, done) {
          if (!file.name.toLowerCase().endsWith(".tgz")) {
            done("The file must be a .tgz archive");
          } else {
            notify(`File ${file.name} accepted for upload.`, "success", 5, true);
            done();
          }
        },
      });
    },
  });
}

configureNamespace("automation", [
  displayDiff,
  copyClipboard,
  displayCalendar,
  downloadRun,
  field,
  openServicePanel,
  pauseTask,
  resumeTask,
  runService,
  runServicesOnTargets,
  schedulerAction,
  showImportServicesPanel,
  showResult,
  showRunServicePanel,
  showRuntimePanel,
  stopRun,
  submitInitialForm,
]);
