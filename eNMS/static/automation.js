/*
global
alertify: false
call: false
cantorPairing: false
CodeMirror: false
createPanel: false
diffview: false
fCall: false
getServiceState: false
initTable: false
JSONEditor: false
page: false
serviceTypes: false
showTypePanel: false
tables: false
workflow: true
*/

let currentRuntime;

// eslint-disable-next-line
function openServicePanel() {
  showTypePanel($("#service-type").val());
}

// eslint-disable-next-line
function panelCode(type, id, mode) {
  const typeInput = $(id ? `#${type}-class-${id}` : `#${type}-class`);
  typeInput.val(type).prop("disabled", true);
  $(id ? `#${type}-name-${id}` : `#${type}-name`).prop("disabled", true);
  if (id) $(`#${type}-shared-${id}`).prop("disabled", true);
  $(id ? `#${type}-workflows-${id}` : `#${type}-workflows`).prop(
    "disabled",
    true
  );
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard({
    autoAdjustHeight: false,
    enableAllSteps: true,
    keyNavigation: false,
    transitionEffect: "none",
  });
  $(".buttonFinish,.buttonNext,.buttonPrevious").hide();
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard("fixHeight");
  if (mode == "run") {
    $(`#${type}-btn-${id}`)
      .removeClass("btn-success")
      .addClass("btn-primary")
      .attr("onclick", `parametrizedRun('${type}', ${id})`)
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
  createPanel("display", "Result", id, function() {
    call(`/get_result/${id}`, (result) => {
      const jsonResult = parseObject(JSON.parse(JSON.stringify(result)));
      const options = {
        mode: "view",
        modes: ["text", "view"],
        onModeChange: function(newMode) {
          editor.set(newMode == "text" ? result : jsonResult);
        },
      };
      let editor = new JSONEditor(
        document.getElementById(`content-${id}`),
        options,
        jsonResult
      );
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
function showRuntimePanel(type, service, runtime) {
  displayFunction =
    type == "logs"
      ? displayLogs
      : service.type == "workflow"
      ? displayResultsTree
      : displayResultsPanel;
  createPanel(
    service.type != "workflow" && type == "results" ? "result" : "runtime",
    `${type} - ${service.name}`,
    service.id,
    function() {
      if (runtime) {
        $(`#div-runtimes-${service.id}`).hide();
        displayFunction(service, runtime);
      } else {
        call(`/get_runtimes/${type}/${service.id}`, (runtimes) => {
          if (!runtimes.length) {
            return alertify.notify(`No ${type} yet.`, "error", 5);
          } else {
            $(`#runtimes-${service.id}`).empty();
            runtimes.forEach((runtime) => {
              $(`#runtimes-${service.id}`).append(
                $("<option></option>")
                  .attr("value", runtime[0])
                  .text(runtime[1])
              );
            });
            if (!runtime || runtime == "normal") {
              runtime = runtimes[runtimes.length - 1][0];
            }
            $(`#runtimes-${service.id}`)
              .val(runtime)
              .selectpicker("refresh");
            displayFunction(service, runtime);
          }
        });
      }
    }
  );
}

function displayLogs(service, runtime) {
  $("#body-runtime").css("background-color", "#1B1B1B");
  const content = document.getElementById(`content-${service.id}`);
  // eslint-disable-next-line new-cap
  let editor = CodeMirror(content, {
    lineWrapping: true,
    lineNumbers: true,
    readOnly: true,
    theme: "cobalt",
    extraKeys: { "Ctrl-F": "findPersistent" },
    scrollbarStyle: "overlay",
  });
  editor.setSize("100%", "100%");
  $(`#runtimes-${service.id}`).on("change", function() {
    refreshLogs(service, this.value, editor);
  });
  refreshLogs(service, runtime, editor, true);
}

function displayResultsTree(service, runtime) {
  call(`/get_workflow_results/${service.id}/${runtime}`, function(data) {
    function customMenu(node) {
      console.log("test");
      var items = {
        item1: {
          label: "item1",
          action: function() {
            /* action */
          },
        },
        item2: {
          label: "item2",
          action: function() {
            /* action */
          },
        },
      };
      return items;
    }
    let tree = $(`#content-${service.id}`).jstree({
      core: {
        animation: 200,
        themes: { stripes: true },
        data: data,
      },
      plugins: ["contextmenu", "types"],
      contextmenu: { items: customMenu },
      types: {
        default: {
          icon: "glyphicon glyphicon-file",
        },
        workflow: {
          icon: "fa fa-sitemap",
        },
      },
    });
    tree.bind("loaded.jstree", function() {
      tree.jstree("open_all");
    });
  });
}

function displayResultsPanel(service, runtime) {
  $("#result").remove();
  $(`#runtimes-${service.id}`).on("change", function() {
    tables["result"].ajax.reload(null, false);
  });
  initTable("result", service, runtime || currentRuntime);
}

// eslint-disable-next-line
function refreshLogs(service, runtime, editor, first, wasRefreshed) {
  if (!$(`#runtime-${service.id}`).length) return;
  call(`/get_service_logs/${runtime}`, function(result) {
    editor.setValue(result.logs);
    editor.setCursor(editor.lineCount(), 0);
    if (first || result.refresh) {
      setTimeout(
        () => refreshLogs(service, runtime, editor, false, result.refresh),
        1000
      );
    } else if (wasRefreshed) {
      $(`#runtime-${service.id}`).remove();
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
function parametrizedRun(type, id) {
  fCall("/run_service", `#edit-${type}-form-${id}`, function(result) {
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

(function() {
  if (page == "table/service" || page == "workflow_builder") {
    $("#service-type").selectpicker({ liveSearch: true });
    for (const [serviceType, serviceName] of Object.entries(serviceTypes)) {
      $("#service-type").append(new Option(serviceName, serviceType));
    }
    $("#service-type").selectpicker("refresh");
  }
})();
