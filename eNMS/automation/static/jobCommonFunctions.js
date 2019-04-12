/*
global
alertify: false
call: false
diffview: false
editService: false
getJobState: false
getWorkflowState: false
jsPanel: false
partial: false
showTypeModal: false
*/

let jobId;
let refresh;
let refreshJob = {};

$("#results-modal").on("hidden.bs.modal", function() {
  refresh = false;
});

/**
 * Open smart wizard.
 * @param {type} type - Service or Workflow.
 */
// eslint-disable-next-line
function openWizard(type) {
  $(`#${type}-wizard`).smartWizard({
    enableAllSteps: true,
    keyNavigation: false,
    transitionEffect: "none",
  });
  if (!$(`#${type}-id`).val()) {
    if (type == "service") {
      editService();
    }
    $(`#${type}-wizard`).smartWizard("goToStep", 1);
  }
  $(".buttonNext").addClass("btn btn-success");
  $(".buttonPrevious").addClass("btn btn-primary");
  $(".buttonFinish").hide();
}

/**
 * Show the editing modal for a job.
 * @param {job} job - Job object.
 */
// eslint-disable-next-line
function editJob(job) {
  if (job.type == "Workflow") {
    showTypeModal("workflow", job.id);
  } else {
    editService(job.id);
  }
}

/**
 * Display result.
 * @param {results} results - Results.
 */
function displayResult(results) {
  const value = results[$("#display").val()];
  if (!value) return;
  $("#results").text(
    JSON.stringify(
      Object.fromEntries(
        Object.entries(value)
          .sort()
          .reverse()
      ),
      null,
      2
    ).replace(/(?:\\[rn]|[\r\n]+)+/g, "\n")
  );
}

/**
 * Display results.
 */
function displayResults() {
  call(`/automation/get_results/${jobId}`, (results) => {
    $("#display,#compare_with").empty();
    const times = Object.keys(results);
    times.forEach((option) => {
      $("#display,#compare_with").append(
        $("<option></option>")
          .attr("value", option)
          .text(option)
      );
    });
    $("#display,#compare_with").val(times[times.length - 1]);
    displayResult(results);
  });
}

/**
 * Refresh results.
 * @param {firstTime} firstTime - First time.
 */
// eslint-disable-next-line
function refreshResults(firstTime) {
  if (firstTime) {
    refresh = !refresh;
    $("#refresh-results-button").text(
      refresh ? "Stop periodic Refresh" : "Trigger periodic Refresh"
    );
  }
  if (refresh) {
    displayResults();
    setTimeout(refreshResults, 5000);
  }
}

/**
 * Display logs.
 * @param {firstTime} firstTime - First time.
 */
// eslint-disable-next-line
function refreshLogs(firstTime, id) {
  if (refreshJob[id]) {
    call(`/automation/get_logs/${id}`, (job) => {
      $(`#logs-${id}`).text(job.logs.join("\n"));
      if (!job.running || $(`#logs-${id}`).length == 0) {
        refreshJob[id] = false;
      }
    });
    setTimeout(partial(refreshLogs, false, id), 500);
  }
}

/**
 * Show the results modal for a job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function showLogs(id) {
  if ($(`#logs-${id}`).length == 0) {
    jsPanel.create({
      theme: "dark filled",
      border: "medium",
      headerTitle: "Logs",
      position: "center-top 0 58",
      contentSize: "650 600",
      content: `<pre id="logs-${id}" style="border: 0;\
        background-color: transparent;"></pre>`,
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
function showResults(id) {
  jobId = id;
  $("#results").empty();
  displayResults();
  $("#results-modal").modal("show");
}

/**
 * Clear the results
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function clearResults() {
  call(`/automation/clear_results/${jobId}`, () => {
    $("#results").empty();
    alertify.notify("Results cleared.", "success", 5);
    $("#results-modal").modal("hide");
  });
}

/**
 * Detach window
 */
// eslint-disable-next-line
function detachWindow() {
  window
    .open(
      `/automation/detach_results/${jobId}`,
      "Results",
      "height=500,width=800"
    )
    .focus();
  $("#results-modal").modal("hide");
}

$("#display").on("change", function() {
  call(`/automation/get_results/${jobId}`, (results) => {
    displayResult(results);
    $("#compare_with").val($("#display").val());
  });
});

$("#compare_with").on("change", function() {
  $("#results").empty();
  const v1 = $("#display").val();
  const v2 = $("#compare_with").val();
  call(`/automation/get_diff/${jobId}/${v1}/${v2}`, function(data) {
    $("#results").append(
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

/**
 * Run job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function runJob(id) {
  call(`/automation/run_job/${id}`, function(job) {
    alertify.notify(`Job '${job.name}' started.`, "success", 5);
    if (typeof workflowBuilder !== "undefined") {
      if (job.type == "Workflow") {
        getWorkflowState();
      } else {
        getJobState(id);
      }
    }
    showLogs(id);
  });
}
