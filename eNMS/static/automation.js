/*
global
alertify: false
call: false
cantorPairing: false
createPanel: false
diffview: false
fCall: false
getServiceState: false
initTable: false
JSONEditor: false
page: false
serviceTypes: false
showTypePanel: false
*/

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

function getRuntimes(type, id) {
  call(`/get_runtimes/${type}/${id}`, (runtimes) => {
    $(`#runtime-${id},#runtime_compare-${id}`).empty();
    runtimes.forEach((runtime) => {
      $(`#runtime-${id},#runtime_compare-${id}`).append(
        $("<option></option>")
          .attr("value", runtime[0])
          .text(runtime[1])
      );
    });
    const mostRecent = runtimes[runtimes.length - 1];
    $(`#runtime-${id},#runtime_compare-${id}`).val(mostRecent);
    $(`#runtime-${id},#runtime_compare-${id}`).selectpicker("refresh");
    if (runtimes) refreshLogs({ id: id }, $(`#runtime-${id}`).val());
  });
}

// eslint-disable-next-line
function showResultsPanel(service, runtime) {
  $("#result").remove();
  createPanel("result", `Results - ${service.name}`, null, function() {
    initTable("result", service, runtime);
  });
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
function refreshLogs(service, runtime, displayResults) {
  if (!$(`#logs-form-${service.id}`).length) return;
  fCall("/get_service_logs", `#logs-form-${service.id}`, function(result) {
    $(`#log-${service.id}`).text(result.logs);
    if (result.refresh) {
      setTimeout(() => refreshLogs(service, runtime, displayResults), 1000);
    } else if (displayResults) {
      $(`#logs-${service.id}`).remove();
      showResultsPanel(service, runtime);
    }
  });
}

// eslint-disable-next-line
function showLogsPanel(service, runtime, displayResults) {
  createPanel("logs", `Logs - ${service.name}`, service.id, function() {
    configureLogsCallbacks(service, runtime);
    if (!runtime) {
      getRuntimes("logs", service.id);
    } else {
      $(`#runtime-${service.id}`)
        .append(`<option value='${runtime}'>${runtime}</option>`)
        .val(runtime)
        .selectpicker("refresh");
      $(`#runtime-div-${service.id}`).hide();
      refreshLogs(service, runtime, displayResults);
    }
  });
}

// eslint-disable-next-line
function configureLogsCallbacks(service, runtime) {
  $(`#filter-${service.id}`).on("input", function() {
    refreshLogs(service, runtime, false);
  });
  if (!runtime) {
    $(`#runtime-${service.id}`).on("change", function() {
      refreshLogs(service, this.value, false);
    });
  }
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
  showLogsPanel(result.service, result.runtime, true);
  alertify.notify(`Service '${result.service.name}' started.`, "success", 5);
  if (page == "workflow_builder" && workflow) {
    if (result.service.id != workflow.id) getServiceState(result.service.id, true);
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
