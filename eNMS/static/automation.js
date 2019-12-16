/*
global
action: true
alertify: false
call: false
cantorPairing: false
CodeMirror: false
createPanel: false
currentPath: true
diffview: false
displayWorkflow: false
editors: true
fCall: false
getServiceState: false
initTable: false
JSONEditor: false
page: false
serviceTypes: false
showPanel: false
showTypePanel: false
tables: false
workflow: true
*/

let currentRuntime;
let arrowHistory = [""];
let arrowPointer = -1;

// eslint-disable-next-line
function openServicePanel() {
  showTypePanel($("#service-type").val());
}

// eslint-disable-next-line
function panelCode(type, id, mode) {
  const typeInput = $(id ? `#${type}-class-${id}` : `#${type}-class`);
  typeInput.val(type).prop("disabled", true);
  $(id ? `#${type}-name-${id}` : `#${type}-name`).prop("disabled", true);
  if (id) {
    $(`#${type}-shared-${id}`).prop("disabled", true);
    if (mode == "duplicate" && type == "workflow") {
      $(`#original-${id}`).val(id);
    }
  }
  $(id ? `#${type}-workflows-${id}` : `#${type}-workflows`).prop(
    "disabled",
    true
  );
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard({
    enableAllSteps: true,
    keyNavigation: false,
    transitionEffect: "none",
    onShowStep: function() {
      Object.keys(editors[id]).forEach(function(field) {
        editors[id][field].refresh();
      });
    },
  });
  $(".buttonFinish,.buttonNext,.buttonPrevious").hide();
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard("fixHeight");
  if (mode == "run") {
    $(`#${type}-btn-${id}`)
      .removeClass("btn-success")
      .addClass("btn-primary")
      .attr("onclick", `parameterizedRun('${type}', ${id})`)
      .text("Run");
    $(".readonly-when-run").prop("readonly", true);
  }
}

function parseObject(obj) {
  for (let k in obj) {
    if (typeof obj[k] === "object" && obj[k] !== null) {
      parseObject(obj[k]);
    } else if (obj.hasOwnProperty(k) && typeof obj[k] === "string") {
      const lines = obj[k].replace(/(?:\\[rn]|[\r\n]+)+/g, "\n").split("\n");
      if (lines.length > 1) obj[k] = lines;
    }
  }
  return obj;
}

// eslint-disable-next-line
function compare(type) {
  const v1 = $("input[name=v1]:checked").val();
  const v2 = $("input[name=v2]:checked").val();
  if (v1 && v2) {
    const cantorId = cantorPairing(parseInt(v1), parseInt(v2));
    createPanel("compare", `Compare ${type}s`, cantorId, () => {
      call(`/compare/${type}/${v1}/${v2}`, (result) => {
        $(`#content-${cantorId}`).append(
          diffview.buildView({
            baseTextLines: result.first,
            newTextLines: result.second,
            opcodes: result.opcodes,
            baseTextName: "V1",
            newTextName: "V2",
            contextSize: null,
            viewType: 0,
          })
        );
      });
    });
  } else {
    alertify.notify("Select two versions to compare first.", "error", 5);
  }
}

// eslint-disable-next-line
function showResult(id) {
  createPanel("result", "Result", id, function() {
    call(`/get_result/${id}`, (result) => {
      const jsonResult = result; //parseObject(JSON.parse(JSON.stringify(result)));
      const options = {
        mode: "view",
        modes: ["code", "view", "form"],
        onModeChange: function(newMode) {
          editor.set(newMode == "code" ? result : jsonResult);
        },
        onClassName: function() {
          return "json-editor-node";
        },
        onEvent(node, event) {
          if (event.type === "click") {
            path = node.path.map((key) =>
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
        el.innerText = el.innerText.replace(/(?:\\n)/g, '\n');
      });
    });
  });
}

// eslint-disable-next-line
function clearResults(id) {
  call(`/clear_results/${id}`, () => {
    alertify.notify("Results cleared.", "success", 5);
    $(`#results-${id}`).remove();
  });
}

// eslint-disable-next-line
function showRuntimePanel(type, service, runtime, displayTable) {
  const displayFunction =
    type == "logs"
      ? displayLogs
      : service.type == "workflow" && !displayTable
      ? displayResultsTree
      : displayResultsTable;
  const panelType =
    type == "logs"
      ? "logs"
      : service.type == "workflow" && !displayTable
      ? "tree"
      : "result_table";
  const panelId = `${panelType}-${service.id}`;
  call(`/get_runtimes/${type}/${service.id}`, (runtimes) => {
    if (!runtime && !runtimes.length) {
      return alertify.notify(`No ${type} yet.`, "error", 5);
    }
    createPanel(panelType, `${type} - ${service.name}`, panelId, function() {
      $(`#runtimes-${panelId}`).empty();
      runtimes.forEach((runtime) => {
        $(`#runtimes-${panelId}`).append(
          $("<option></option>")
            .attr("value", runtime[0])
            .text(runtime[1])
        );
      });
      if (!runtime || runtime == "normal") {
        runtime = runtimes[runtimes.length - 1][0];
      }
      $(`#runtimes-${panelId}`)
        .val(runtime)
        .selectpicker("refresh");
      $(`#runtimes-${panelId}`).on("change", function() {
        displayFunction(service, this.value, true);
      });
      displayFunction(service, runtime);
    });
  });
}

function displayLogs(service, runtime, change) {
  $(`#body-runtime-logs-${service.id}`).css("background-color", "#1B1B1B");
  const content = document.getElementById(`content-logs-${service.id}`);
  let editor;
  if (change) {
    editor = $(`#content-logs-${service.id}`).data("CodeMirrorInstance");
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
      scrollbarStyle: "overlay",
    });
    $(`#content-logs-${service.id}`).data("CodeMirrorInstance", editor);
    editor.setSize("100%", "100%");
  }
  $(`#runtimes-logs-${service.id}`).on("change", function() {
    refreshLogs(service, this.value, editor);
  });
  refreshLogs(service, runtime, editor, true);
}

function displayResultsTree(service, runtime) {
  call(`/get_workflow_results/${service.id}/${runtime}`, function(data) {
    $(`#result-tree-tree-${service.id}`)
      .jstree("destroy")
      .empty();
    let tree = $(`#result-tree-tree-${service.id}`).jstree({
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
        default: function(el, node) {
          if (!node) return;
          const data = JSON.stringify(node.data.properties);
          if (node.data.progress) {
            progressSummary = `
              <div style="position: absolute; top: 0px; right: 200px">
                <span style="color: #32cd32">${
                  node.data.progress.success
                } passed</span> -
                <span style="color: #FF6666">${
                  node.data.progress.failure
                } failed</span>
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
                onclick='showRuntimePanel("logs", ${data}, "${runtime}")'
              >
                <span class="glyphicon glyphicon-list"></span>
              </button>
              <button type="button"
                class="btn btn-xs btn-primary"
                onclick='showRuntimePanel("results", ${data}, "${runtime}", true)'
              >
                <span class="glyphicon glyphicon-list-alt"></span>
              </button>
            </div>
          `);
        },
      },
    });
    tree.bind("loaded.jstree", function() {
      tree.jstree("open_all");
    });
    tree.unbind("dblclick.jstree").bind("dblclick.jstree", function(event) {
      const service = tree.jstree().get_node(event.target);
      showRuntimePanel("results", service.data.properties, runtime, true);
    });
  });
}

function displayResultsTable(service, runtime) {
  $("#result_table").remove();
  $(`#runtimes-result-${service.id}`).on("change", function() {
    tables[`result-${service.id}`].ajax.reload(null, false);
  });
  initTable(
    "result",
    service,
    runtime || currentRuntime,
    `result_table-${service.id}`
  );
}

// eslint-disable-next-line
function refreshLogs(service, runtime, editor, first, wasRefreshed) {
  if (!$(`#runtimes-logs-${service.id}`).length) return;
  call(`/get_service_logs/${service.id}/${runtime}`, function(result) {
    editor.setValue(result.logs);
    editor.setCursor(editor.lineCount(), 0);
    if (first || result.refresh) {
      setTimeout(
        () => refreshLogs(service, runtime, editor, false, result.refresh),
        1000
      );
    } else if (wasRefreshed) {
      $(`#runtime-logs-${service.id}`).remove();
      showRuntimePanel("results", service, runtime);
    }
  });
}

// eslint-disable-next-line
function normalRun(id) {
  call(`/run_service/${id}`, function(result) {
    runLogic(result);
  });
}

// eslint-disable-next-line
function parameterizedRun(type, id) {
  fCall("/run_service", `edit-${type}-form-${id}`, function(result) {
    $(`#${type}-${id}`).remove();
    runLogic(result);
  });
}

function runLogic(result) {
  showRuntimePanel("logs", result.service, result.runtime);
  alertify.notify(`Service '${result.service.name}' started.`, "success", 5);
  if (page == "workflow_builder" && workflow) {
    if (result.service.id != workflow.id) {
      getServiceState(result.service.id, true);
    }
  }
  $(`#${result.service.type}-${result.service.id}`).remove();
}

// eslint-disable-next-line
function exportService(id) {
  call(`/export_service/${id}`, () => {
    alertify.notify("Export successful.", "success", 5);
  });
}

// eslint-disable-next-line
function pauseTask(id) {
  // eslint-disable-line no-unused-vars
  call(`/task_action/pause/${id}`, function(result) {
    $(`#pause-resume-${id}`)
      .attr("onclick", `resumeTask('${id}')`)
      .text("Resume");
    alertify.notify("Task paused.", "success", 5);
  });
}

// eslint-disable-next-line
function resumeTask(id) {
  // eslint-disable-line no-unused-vars
  call(`/task_action/resume/${id}`, function() {
    $(`#pause-resume-${id}`)
      .attr("onclick", `pauseTask('${id}')`)
      .text("Pause");
    alertify.notify("Task resumed.", "success", 5);
  });
}

function switchToWorkflow(path, arrow) {
  if (typeof path === "undefined") return;
  if (path.toString().includes(">")) {
    $("#up-arrow").removeClass("disabled");
  } else {
    $("#up-arrow").addClass("disabled");
  }
  currentPath = path;
  if (!arrow) {
    arrowPointer++;
    arrowHistory.splice(arrowPointer, 9e9, currentPath);
  } else {
    arrowPointer += arrow == "right" ? 1 : -1;
  }
  if (arrowHistory.length >= 1 && arrowPointer !== 0) {
    $("#left-arrow").removeClass("disabled");
  } else {
    $("#left-arrow").addClass("disabled");
  }
  if (arrowPointer < arrowHistory.length - 1) {
    $("#right-arrow").removeClass("disabled");
  } else {
    $("#right-arrow").addClass("disabled");
  }
  if (page == "workflow_builder") {
    call(`/get_service_state/${currentPath}/latest`, function(result) {
      workflow = result.service;
      displayWorkflow(result);
      alertify.notify(
        `Workflow '${workflow.scoped_name}' displayed.`,
        "success",
        5
      );
    });
  } else {
    $("#workflow-filtering").val(currentPath);
    if (tables["service"]) tables["service"].ajax.reload(null, false);
  }
}

// eslint-disable-next-line
function field(name, type, id) {
  const fieldId = id ? `${type}-${name}-${id}` : `${type}-${name}`;
  return $(`#${fieldId}`);
}

// eslint-disable-next-line
function displayCalendar(calendarType) {
  showPanel("calendar", calendarType, () => {
    call(`/calendar_init/${calendarType}`, function(tasks) {
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
        eventClick: function(e) {
          if (calendarType == "task") {
            showTypePanel("task", e.id);
          } else {
            showRuntimePanel("results", e.service, e.runtime);
          }
        },
        editable: true,
        events: events,
      });
    });
  });
}

Object.assign(action, {
  Edit: (service) => showTypePanel(service.type, service.id),
  Duplicate: (service) => showTypePanel(service.type, service.id, "duplicate"),
  Run: (service) => normalRun(service.id),
  "Parameterized Run": (service) =>
    showTypePanel(service.type, service.id, "run"),
  Results: (service) => showRuntimePanel("results", service),
  Backward: () => switchToWorkflow(arrowHistory[arrowPointer - 1], "left"),
  Forward: () => switchToWorkflow(arrowHistory[arrowPointer + 1], "right"),
});

(function() {
  if (page == "table/service" || page == "workflow_builder") {
    $("#service-type").selectpicker({ liveSearch: true });
    for (const [serviceType, serviceName] of Object.entries(serviceTypes)) {
      $("#service-type").append(new Option(serviceName, serviceType));
    }
    $("#service-type").selectpicker("refresh");
  }
  if (page == "table/service") switchToWorkflow("");
})();
