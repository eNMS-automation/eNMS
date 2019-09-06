/*
global
alertify: false
call: false
createPanel: false
diffview: false
displayWorkflow: false
fCall: false
getJobState: false
JSONEditor: false
page: false
saveWorkflowJob: false
showTypePanel: false
table: false
*/

let currentResults = {};

// eslint-disable-next-line
function openServicePanel() {
  showTypePanel($("#service-type").val());
}

// eslint-disable-next-line
function panelCode(type, id, mode) {
  const typeInput = $(id ? `#${type}-class-${id}` : `#${type}-class`);
  typeInput.val(type).prop("disabled", true);
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard({
    autoAdjustHeight: false,
    enableAllSteps: true,
    keyNavigation: false,
    transitionEffect: "none",
  });
  $(`#${type}-workflows-${id} option`).prop("disabled", true);
  $(".buttonFinish,.buttonNext,.buttonPrevious").hide();
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard("fixHeight");
  if (mode == "run") {
    $(`#${type}-btn-${id}`)
      .removeClass("btn-success")
      .addClass("btn-primary")
      .attr("onclick", `parametrizedRun('${type}', ${id})`)
      .text("Run");
    $(".hide-run").hide();
  } else {
    $(".no-edit").remove();
  }
}

// eslint-disable-next-line
function workflowRunMode(instance, restartForm) {
  call(`/get_runtimes/workflow/${instance.id}`, function(runtimes) {
    const versionId = restartForm
      ? "#restart_runtime"
      : `#workflow-restart_runtime-${instance.id}`;
    runtimes.forEach((runtime) => {
      $(versionId).append(
        $("<option></option>")
          .attr("value", runtime[0])
          .text(runtime[0])
      );
    });
    $(versionId).val(runtimes[runtimes.length - 1]);
    $(versionId).selectpicker("refresh");
  });
}

// eslint-disable-next-line
function saveService(job, id) {
  if (page == "workflow_builder") {
    saveWorkflowJob(job, id);
  }
}

// eslint-disable-next-line
function saveWorkflow(newWorkflow) {
  if (page == "workflow_builder") {
    $("#current-workflow").append(
      `<option value="${newWorkflow.id}">${newWorkflow.name}</option>`
    );
    $("#current-workflow").val(newWorkflow.id);
    $("#current-workflow").selectpicker("refresh");
    displayWorkflow({ workflow: newWorkflow, runtimes: [] });
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

function formatResults(results, id, formId, compare) {
  if (!results) results = currentResults;
  if (!results) {
    $(`#display_results-${formId}`).text("No results yet.");
  } else if (compare) {
    $(`#display_results-${formId}`).empty();
    $(`#display_results-${formId}`).append(
      diffview.buildView({
        baseTextLines: results.first,
        newTextLines: results.second,
        opcodes: results.opcodes,
        baseTextName: $(`#runtime-${id}`).val(),
        newTextName: $(`#runtime_compare-${id}`).val(),
        contextSize: null,
        viewType: 0,
      })
    );
  } else {
    $(`#display_results-${formId}`).empty();
    const textResults = JSON.parse(JSON.stringify(results));
    const jsonResults = parseObject(JSON.parse(JSON.stringify(results)));
    const options = {
      mode: $(`#view_type-${id}`).val(),
      modes: ["text", "view"],
      onModeChange: function(newMode) {
        editor.set(newMode == "text" ? textResults : jsonResults);
      },
    };
    let editor = new JSONEditor(
      document.getElementById(`display_results-${formId}`),
      options,
      $(`#view_type-${formId}`).val() == "text" ? textResults : jsonResults
    );
  }
}

function displayResults(type, id, formId, compare) {
  const url = compare ? "compare" : "get";
  if ($(`#runtime-${id}`).val() || type == "run") {
    fCall(
      `/${url}_results/${type}/${id}`,
      `#results-form-${formId}`,
      (results) => {
        currentResults = results;
        formatResults(results, id, formId, compare);
      }
    );
  } else {
    $(`#display_results-${formId}`).text("No results yet.");
  }
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
function showResultsPanel(job) {
  $("#result").remove();
  createPanel("result", `Results - ${job.name}`, null, function() {
    resultTable = initTable("result", true);
  });
}

// eslint-disable-next-line
function showResult(id) {
  createPanel(`display_result`, "Result", id, function() {
    call(`/get_result/${id}`, (result) => {
      const textResults = JSON.parse(JSON.stringify(result));
      const options = {
        mode: "view",
        modes: ["text", "view"],
        onModeChange: function(newMode) {
          editor.set(textResults);
        },
      };
      let editor = new JSONEditor(
        document.getElementById(`display_results-${id}`),
        options,
        textResults
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
function refreshLogs(job, runtime, displayResults) {
  if (!$(`#logs-form-${job.id}`).length) return;
  fCall("/get_job_logs", `#logs-form-${job.id}`, function(result) {
    $(`#log-${job.id}`).text(result.logs);
    if (result.refresh) {
      setTimeout(() => refreshLogs(job, runtime, displayResults), 1500);
    } else if (displayResults) {
      $(`#logs-${job.id}`).remove();
      showResultsPanel(job.id, job.name, runtime);
    }
  });
}

// eslint-disable-next-line
function showLogsPanel(job, runtime, displayResults) {
  createPanel("logs", `Logs - ${job.name}`, job.id, function() {
    configureLogsCallbacks(job, runtime);
    if (!runtime) {
      getRuntimes("logs", job.id);
    } else {
      $(`#runtime-${job.id}`)
        .append(`<option value='${runtime}'>${runtime}</option>`)
        .val(runtime)
        .selectpicker("refresh");
      $(`#runtime-div-${job.id}`).hide();
      refreshLogs(job, runtime, displayResults);
    }
  });
}

// eslint-disable-next-line
function configureLogsCallbacks(job, runtime) {
  $(`#filter-${job.id}`).on("input", function() {
    refreshLogs(job, runtime, false);
  });
  if (!runtime) {
    $(`#runtime-${job.id}`).on("change", function() {
      refreshLogs(job, this.value, false);
    });
  }
}

// eslint-disable-next-line
function normalRun(id) {
  call(`/run_job/${id}`, function(job) {
    runLogic(job);
  });
}

// eslint-disable-next-line
function parametrizedRun(type, id) {
  fCall("/run_job", `#edit-${type}-form-${id}`, function(job) {
    $(`#${type}-${id}`).remove();
    runLogic(job);
  });
}

function runLogic(job) {
  showLogsPanel(job, job.runtime, true);
  alertify.notify(`Job '${job.name}' started.`, "success", 5);
  if (page == "workflow_builder") {
    if (job.type != "workflow") {
      getJobState(job.id);
    }
  }
  $(`#${job.type}-${job.id}`).remove();
}

// eslint-disable-next-line
function duplicateWorkflow(id) {
  fCall(
    `/duplicate_workflow/${id}`,
    `#edit-workflow-form-${id}`,
    (workflow) => {
      table.ajax.reload(null, false);
      $(`#workflow-${id}`).remove();
      alertify.notify("Workflow successfully duplicated.", "success", 5);
    }
  );
}

// eslint-disable-next-line
function exportJob(id) {
  call(`/export_job/${id}`, () => {
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
  call(`/task_action/resume/${id}`, function(result) {
    $(`#pause-resume-${id}`)
      .attr("onclick", `pauseTask('${id}')`)
      .text("Pause");
    alertify.notify("Task resumed.", "success", 5);
  });
}

(function() {
  if (page == "table/service" || page == "workflow_builder") {
    $("#service-type").selectpicker({
      liveSearch: true,
    });
  }
})();
