/*
global
action: true
CodeMirror: false
Diff2HtmlUI: false
Dropzone: false
formProperties: true
JSONEditor: false
jsPanel: false
page: false
serviceTypes: false
*/

import {
  call,
  cantorPairing,
  configureForm,
  configureNamespace,
  downloadFile,
  notify,
  observeMutations,
  openPanel,
  serializeForm,
  showInstancePanel,
} from "./base.js";
import { refreshTable, tableInstances, tables } from "./table.js";
import {
  arrowHistory,
  arrowPointer,
  currentRuntime,
  getServiceState,
  switchToWorkflow,
  workflow,
} from "./workflowBuilder.js";

function openServicePanel(bulk) {
  showInstancePanel($("#service-type").val(), null, bulk ? "bulk" : null, "service");
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

function downloadLogs(serviceId) {
  const logs = $(`#service-logs-${serviceId}`).data("CodeMirrorInstance").getValue();
  downloadFile(`logs-${serviceId}`, logs, "txt");
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
            element.innerText = element.innerText.replace(/(?:\\n)/g, "\n");
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
  if (!runtime) runtime = currentRuntime;
  const displayFunction =
    type == "logs"
      ? displayLogs
      : service.type == "workflow" && !table
      ? displayResultsTree
      : displayResultsTable;
  const panelType =
    type == "logs" ? "logs" : service.type == "workflow" && !table ? "tree" : "table";
  const panelId = `${panelType}-${service.id}`;
  call({
    url: `/get_runtimes/${type}/${service.id}`,
    callback: (runtimes) => {
      if (newRuntime) runtimes.push([runtime, runtime]);
      if (!runtimes.length) return notify(`No ${type} yet.`, "error", 5);
      let content;
      if (panelType == "logs") {
        content = `
        <div class="modal-body">
          <nav
            id="controls"
            class="navbar navbar-default nav-controls"
            role="navigation"
          >
            <div style="width: 85%; float: left;">
              <select
                id="runtimes-${panelId}"
                name="runtimes"
                class="form-control"
              ></select>
            </div>
            <div style="width: 10%; float: left;  margin-left: 15px;">
              <button
                class="btn btn-default pull-right"
                onclick="eNMS.automation.downloadLogs(${service.id})"
                data-tooltip="Update all pools"
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
        content = `
        <div class="modal-body">
          <select
            id="runtimes-${panelId}"
            name="runtimes"
            class="form-control"
          ></select>
          <hr>
          <div id="result-${panelId}" style="height: 500px"></div>
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
                color:transparent; width: 250px;"
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
        type: "result",
        title: `${type} - ${service.name}`,
        id: service.id,
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

function displayLogs(service, runtime, change) {
  const content = document.getElementById(`service-logs-${service.id}`);
  let editor;
  if (change) {
    editor = $(`#service-logs-${service.id}`).data("CodeMirrorInstance");
    editor.setValue("");
  } else {
    // eslint-disable-next-line new-cap
    editor = CodeMirror(content, {
      lineWrapping: true,
      lineNumbers: true,
      readOnly: true,
      theme: "cobalt",
      mode: "logs",
      extraKeys: { "Ctrl-F": "findPersistent" },
    });
    $(`#service-logs-${service.id}`).data("CodeMirrorInstance", editor);
    editor.setSize("100%", "100%");
  }
  $(`#runtimes-logs-${service.id}`).on("change", function () {
    refreshLogs(service, this.value, editor);
  });
  refreshLogs(service, runtime, editor, true);
}

function displayResultsTree(service, runtime) {
  call({
    url: `/get_workflow_results/${service.id}/${runtime}`,
    callback: function (data) {
      $(`#result-tree-${service.id}`).jstree("destroy").empty();
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
    url: `/get_service_logs/${service.id}/${runtime}/${line || 0}`,
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
          1000
        );
      } else if (wasRefreshed) {
        setTimeout(() => {
          $(`#logs-${service.id}`).remove();
          const table = service.type == "workflow" ? null : "result";
          showRuntimePanel("results", service, runtime, table);
        }, 1000);
      }
    },
  });
}

function submitInitialForm(serviceId) {
  call({
    url: `/run_service/${serviceId}`,
    form: `initial-${serviceId}-form-${serviceId}`,
    callback: runLogic,
  });
}

export const runService = function ({ id, form, type }) {
  if (form) {
    openPanel({
      id: id,
      url: `initial_form/${id}`,
      title: "Initial Form",
      size: "700px 600px",
      callback: function () {
        call({
          url: `/get_form_properties/initial-${id}`,
          callback: function (properties) {
            formProperties[`initial-${id}`] = properties;
            configureForm(`initial-${id}`, id);
          },
        });
      },
    });
  } else {
    call({
      url: `/run_service/${id}`,
      form: type ? `${type}-form-${id}` : null,
      callback: function (result) {
        if (type) $(`#${type}-${id}`).remove();
        runLogic(result);
      },
    });
  }
};

export function runLogic(result) {
  const service = result.service.superworkflow || result.service;
  showRuntimePanel("logs", service, result.runtime, undefined, true);
  notify(`Service '${service.name}' started.`, "success", 5, true);
  if (page == "workflow_builder" && workflow) {
    if (service != result.service) {
      switchToWorkflow(service.id, null, result.runtime);
    } else if (result.service.id != workflow.id) {
      getServiceState(result.service.id, true);
    } else {
      $("#current-runtime")
        .append(
          `<option value='${result.runtime}'>
          ${result.runtime}
        </option>`
        )
        .val(result.runtime)
        .selectpicker("refresh");
    }
  }
  $(`#${result.service.type}-${result.service.id}`).remove();
}

function exportServices(tableId) {
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
    callback: function (result) {
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

function field(name, type, id) {
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
            if (properties.service === undefined) continue;
            events.push({
              title: name,
              id: properties.id,
              description: properties.description,
              start: new Date(...properties.start),
              runtime: properties.runtime,
              service: properties.service,
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
  Run: (service) => runService({ id: service.id, form: service.initial_form }),
  "Parameterized Run": (service) =>
    showInstancePanel(service.type, service.id, "run", null, service.initial_form),
  Logs: (service) => showRuntimePanel("logs", service, currentRuntime),
  Results: (service) => showRuntimePanel("results", service, currentRuntime, "result"),
  Backward: () => switchToWorkflow(arrowHistory[arrowPointer - 1], "left"),
  Forward: () => switchToWorkflow(arrowHistory[arrowPointer + 1], "right"),
});

export function loadServiceTypes() {
  $("#service-type").selectpicker({ liveSearch: true });
  for (const [serviceType, serviceName] of Object.entries(serviceTypes)) {
    $("#service-type").append(new Option(serviceName, serviceType));
  }
  $("#service-type").selectpicker("refresh");
}

export function deleteCorruptedEdges() {
  call({
    url: "/delete_corrupted_edges",
    callback: function (number) {
      notify(`${number} Corrupted edges successfully deleted.`, "success", 5);
    },
  });
}

export function showRunServicePanel({ instance, tableId, type }) {
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
      if (type) {
        let form = serializeForm(`#search-form-${panelId}`, `${type}_filtering`);
        if (table) form = { ...form, ...table.constraints };
        call({
          url: `/filtering/${type}`,
          data: { form: form, bulk: "id" },
          callback: function (instances) {
            $(`#run_service-targets-${panelId}`).val(instances.join("-"));
          },
        });
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
    size: "600 350",
    callback: () => {
      call({
        url: "/get_exported_services",
        callback: function (services) {
          const element = document.getElementById(`dropzone-services`);
          new Dropzone(element, {
            url: "/import_services",
            accept: function (file, done) {
              if (!file.name.includes(".tgz")) {
                notify("The file must be a .tgz archive", "error", 5);
              } else {
                done();
              }
            },
          });
        },
      });
    },
  });
}

configureNamespace("automation", [
  displayDiff,
  copyClipboard,
  deleteCorruptedEdges,
  displayCalendar,
  downloadLogs,
  exportServices,
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
  submitInitialForm,
]);
