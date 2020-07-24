/*
global
action: true
CodeMirror: false
Diff2HtmlUI: false
JSONEditor: false
jsPanel: false
page: false
serviceTypes: false
*/

import {
  call,
  cantorPairing,
  configureNamespace,
  notify,
  openPanel,
  showTypePanel,
} from "./base.js";
import { tables } from "./table.js";
import {
  arrowHistory,
  arrowPointer,
  currentRuntime,
  getServiceState,
  switchToWorkflow,
  workflow,
} from "./workflow.js";

function openServicePanel() {
  showTypePanel($("#service-type").val());
}

export function compare(type, instance) {
  const objectType = type.includes("result") ? "result" : type;
  const v1 = $(`input[name=v1-${type}-${instance.id}]:checked`).val();
  const v2 = $(`input[name=v2-${type}-${instance.id}]:checked`).val();
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
          style="margin-top: 5px"
        >
          <input
            id="diff-type-${cantorId}"
            type="checkbox"
            data-onstyle="info"
            data-offstyle="primary"
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
        call({
          url: `/compare/${objectType}/${instance.name}/${v1}/${v2}`,
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
                $(".d2h-file-header").hide();
              })
              .change();
          },
        });
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
        <input id="link-${id}" type="text" class="form-control"
        value='${link}'>
        <span class="input-group-btn">
          <button class="btn btn-default"
            onclick="eNMS.base.copyToClipboard('link-${id}', true)"
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

function showResult(id) {
  openPanel({
    name: "result",
    content: `
      <input
        id="result-path-${id}"
        type="text"
        class="form-control"
        style="height:5%"
        value="results"
      >
      <div id="content-${id}" style="height:95%"></div>`,
    title: "Result",
    id: id,
    callback: function () {
      call({
        url: `/get_result/${id}`,
        callback: (result) => {
          const jsonResult = result;
          const options = {
            mode: "view",
            modes: ["code", "view"],
            onModeChange: function (newMode) {
              editor.set(newMode == "code" ? result : jsonResult);
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
          let editor = new JSONEditor(
            document.getElementById(`content-${id}`),
            options,
            jsonResult
          );
          document.querySelectorAll(".jsoneditor-string").forEach((el) => {
            el.innerText = el.innerText.replace(/(?:\\n)/g, "\n");
          });
        },
      });
    },
  });
}

export const showRuntimePanel = function (type, service, runtime, table) {
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
      if (!runtime && !runtimes.length) {
        return notify(`No ${type} yet.`, "error", 5);
      }
      let content;
      if (panelType == "logs") {
        content = `
        <div class="modal-body">
          <select
            id="runtimes-${panelId}"
            name="runtimes"
            class="form-control"
          ></select>
          <hr>
          <div id="service-${panelId}"></div>
        </div>`;
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
            ></nav>
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
          if (!runtime && page == "workflow_builder") {
            runtime = $("#current-runtime").val();
          }
          if (!runtime || ["normal", "latest"].includes(runtime)) {
            runtime = runtimes[runtimes.length - 1][0];
          }
          $(`#runtimes-${panelId}`).val(runtime).selectpicker("refresh");
          $(`#runtimes-${panelId}`).on("change", function () {
            displayFunction(service, this.value, true, table);
          });
          displayFunction(service, runtime, null, table);
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
            $(el).find("a").append(`
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

function displayResultsTable(service, runtime, _, table) {
  // eslint-disable-next-line new-cap
  table = table ?? "result";
  new tables[table](table, service, runtime || currentRuntime, service.id);
}

function refreshLogs(service, runtime, editor, first, wasRefreshed) {
  if (!$(`#service-logs-${service.id}`).length) return;
  call({
    url: `/get_service_logs/${service.id}/${runtime}`,
    callback: function (result) {
      editor.setValue(result.logs);
      editor.setCursor(editor.lineCount(), 0);
      if (first || result.refresh) {
        setTimeout(
          () => refreshLogs(service, runtime, editor, false, result.refresh),
          1000
        );
      } else if (wasRefreshed) {
        $(`#logs-${service.id}`).remove();
        const table = service.type == "workflow" ? null : "result";
        showRuntimePanel("results", service, runtime, table);
      }
    },
  });
}

export const normalRun = function (id) {
  call({
    url: `/run_service/${id}`,
    callback: function (result) {
      runLogic(result);
    },
  });
};

function parameterizedRun(type, id) {
  call({
    url: `/run_service/${id}`,
    form: `edit-${type}-form-${id}`,
    callback: function (result) {
      $(`#${type}-${id}`).remove();
      runLogic(result);
    },
  });
}

export function runLogic(result) {
  const service = result.service.superworkflow || result.service;
  showRuntimePanel("logs", service, result.runtime);
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

function exportService(id) {
  call({
    url: `/export_service/${id}`,
    callback: () => {
      notify("Service Export successful.", "success", 5, true);
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
                showTypePanel("task", e.id);
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
    callback: function () {
      notify(`Scheduler ${action}d.`, "success", 5, true);
    },
  });
}

Object.assign(action, {
  Edit: (service) => showTypePanel(service.type, service.id),
  Duplicate: (service) => showTypePanel(service.type, service.id, "duplicate"),
  Run: (service) => normalRun(service.id),
  "Parameterized Run": (service) => showTypePanel(service.type, service.id, "run"),
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

configureNamespace("automation", [
  compare,
  copyClipboard,
  deleteCorruptedEdges,
  displayCalendar,
  exportService,
  field,
  normalRun,
  openServicePanel,
  parameterizedRun,
  pauseTask,
  resumeTask,
  schedulerAction,
  showResult,
  showRuntimePanel,
]);
