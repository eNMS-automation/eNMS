/*
global
alertify: false
call: false
createPanel: false
diffview: false
fCall: false
getJobState: false
getWorkflowState: false
jsPanel: false
nodes: true
page: false
showTypePanel: false
table: false
*/

let refreshJob = {};

/**
 * Open service panel
 */
// eslint-disable-next-line
function openServicePanel() {
  showTypePanel($("#service-type").val());
}

/**
 * Custom code upon opening panel.
 * @param {type} type - Service or Workflow.
 */
// eslint-disable-next-line
function panelCode(type, id) {
  const typeInput = $(id ? `#${type}-class-${id}` : `#${type}-class`);
  typeInput.val(type).prop("disabled", true);
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard({
    autoAdjustHeight: false,
    enableAllSteps: true,
    keyNavigation: false,
    transitionEffect: "none",
  });
  $(".buttonFinish,.buttonNext,.buttonPrevious").hide();
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard("fixHeight");
}

/**
 * Save a service.
 * @param {service} service - Service instance.
 */
// eslint-disable-next-line
function saveService(service) {
  if (typeof workflowBuilder !== "undefined") {
    nodes.update({ id: service.id, label: service.name });
  }
}

function parseObject(obj) {
  for (var k in obj) {
    if (typeof obj[k] === 'object' && obj[k] !== null) {
      parseObject(obj[k])
    } else if (obj.hasOwnProperty(k) && typeof obj[k] === 'string') {
      obj[k] = obj[k].replace(/(?:\\[rn]|[\r\n]+)+/g, "\n").split("\n");
    }
  }
  return obj;
}

/**
 * Display result.
 * @param {results} results - Results.
 * @param {id} id - Job id.
 */
function displayResult(results, id) {
  const value = results[$(`#display-${id}`).val()];
  if (!value) {
    $(`#display_results-${id}`).text("No results yet.");
  }
  else if (false) {
    let container = document.getElementById(`display_results-${id}`);
    const options = { mode: 'view' };
    let editor = new JSONEditor(container, options, parseObject(value));
  } else {
    $(`#display_results-${id}`).html(
      `<pre>${
        JSON.stringify(
          Object.fromEntries(
            Object.entries(value)
              .sort()
              .reverse()
          ),
          null,
          2
        ).replace(/(?:\\[rn]|[\r\n]+)+/g, "\n")
      }</pre>`
    );
  }
}

/**
 * Display results.
 * @param {id} id - Job id.
 */
function displayResults(id) {
  call(`/get_job_results/${id}`, (results) => {
    $(`#display-${id},#compare_with-${id}`).empty();
    const times = Object.keys(results);
    times.forEach((option) => {
      $(`#display-${id},#compare_with-${id}`).append(
        $("<option></option>")
          .attr("value", option)
          .text(option)
      );
    });

    $(`#display-${id},#compare_with-${id}`).val(times[times.length - 1]);
    $(`#display-${id},#compare_with-${id}`).selectpicker("refresh");
    displayResult(results, id);
  });
}

/**
 * Display logs.
 * @param {firstTime} firstTime - First time.
 */
// eslint-disable-next-line
function refreshLogs(firstTime, id) {
  if (refreshJob[id]) {
    call(`/get_job_logs/${id}`, (job) => {
      $(`#logs-${id}`).text(job.logs.join("\n"));
      if (!job.running || $(`#logs-${id}`).length == 0) {
        refreshJob[id] = false;
      }
    });
    setTimeout(() => refreshLogs(false, id), 500);
  }
}

/**
 * Show the results modal for a job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function showLogs(id, name) {
  if ($(`#logs-${id}`).length == 0) {
    jsPanel.create({
      theme: "dark filled",
      border: "medium",
      headerTitle: `Logs - ${name}`,
      position: "center-top 0 58",
      contentSize: "650 600",
      contentOverflow: "hidden scroll",
      content: `<pre id="logs-${id}" style="border: 0;\
        background-color: transparent; color: white;"></pre>`,
      dragit: {
        opacity: 0.7,
        containment: [5, 5, 5, 5],
      },
    });
  }
  refreshJob[id] = true;
  refreshLogs(true, id);
}

/**
 * Show the results modal for a job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function showResultsPanel(id, name) {
  createPanel("results", `Results - ${name}`, id, function() {
    configureCallbacks(id);
    displayResults(id);
  });
}

/**
 * Configure display & comparison callbacks
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function configureCallbacks(id) {
  $(`#display-${id}`).on("change", function() {
    call(`/get_job_results/${id}`, (results) => {
      displayResult(results, id);
      $(`#compare_with-${id}`).val($(`#display-${id}`).val());
    });
  });

  $(`#compare_with-${id}`).on("change", function() {
    $(`#display_results-${id}`).empty();
    const v1 = $(`#display-${id}`).val();
    const v2 = $(`#compare_with-${id}`).val();
    call(`/get_results_diff/${id}/${v1}/${v2}`, function(data) {
      $(`#display_results-${id}`).append(
        diffview.buildView({
          baseTextLines: data.first,
          newTextLines: data.second,
          opcodes: data.opcodes,
          baseTextName: `${v1}`,
          newTextName: `${v2}`,
          contextSize: null,
          viewType: 0,
        })
      );
    });
  });
}

/**
 * Clear the results
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function clearResults(id) {
  call(`/clear_results/${id}`, () => {
    $(`#display_results-${id},#compare_with-${id},#display-${id}`).empty();
    alertify.notify("Results cleared.", "success", 5);
    $(`#results-${id}`).remove();
  });
}

/**
 * Run job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function runJob(id, realTimeUpdate) {
  call(`/run_job/${id}`, function(job) {
    alertify.notify(`Job '${job.name}' started.`, "success", 5);
    if (typeof workflowBuilder !== "undefined") {
      if (job.type == "Workflow") {
        getWorkflowState();
      } else {
        getJobState(id);
      }
    }
    if (realTimeUpdate) showLogs(id);
  });
}

/**
 * Display instance modal for editing.
 * @param {id} id - Instance ID.
 */
// eslint-disable-next-line
function showWorkflowModalDuplicate(id) {
  $("#workflow-button").attr("onclick", `duplicateWorkflow(${id})`);
  showTypePanel("workflow", id, true);
}

/**
 * Display instance modal for editing.
 * @param {id} id - Instance ID.
 */
// eslint-disable-next-line
function duplicateWorkflow(id) {
  $("#edit-workflow").modal("hide");
  fCall(`/duplicate_workflow/${id}`, "#edit-workflow-form", (workflow) => {
    table.ajax.reload(null, false);
    alertify.notify("Workflow successfully duplicated", "success", 5);
  });
}

/**
 * Pause a task.
 * @param {id} id - Task id.
 */
// eslint-disable-next-line
function pauseTask(id) {
  // eslint-disable-line no-unused-vars
  call(`/pause_task/${id}`, function(result) {
    $(`#pause-resume-${id}`)
      .attr("onclick", `resumeTask('${id}')`)
      .text("Resume");
    alertify.notify("Task paused.", "success", 5);
  });
}

/**
 * Resume a task.
 * @param {id} id - Task id.
 */
// eslint-disable-next-line
function resumeTask(id) {
  // eslint-disable-line no-unused-vars
  call(`/resume_task/${id}`, function(result) {
    $(`#pause-resume-${id}`)
      .attr("onclick", `pauseTask('${id}')`)
      .text("Pause");
    alertify.notify("Task resumed.", "success", 5);
  });
}

(function() {
  if (page == "table-service") {
    $("#service-type").selectpicker({
      liveSearch: true,
    });
  }
})();
