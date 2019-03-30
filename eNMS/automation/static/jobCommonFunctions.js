/*
global
alertify: false
call: false
diffview: false
getJobState: false
getWorkflowState: false
*/

let jobId;
let refresh;

$("#logs-modal").on("hidden.bs.modal", function() {
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
    transitionEffect: 'node',
  });
  $(`#${type}-wizard`).smartWizard("goToStep", 1)
  $(".buttonNext").addClass("btn btn-success");
  $(".buttonPrevious").addClass("btn btn-primary");
  $(".buttonFinish").hide();
}

/**
 * Display log.
 * @param {logs} logs - Logs.
 */
function displayLog(logs) {
  const displayLogs = logs[$("#display").val()];
  if (displayLogs) {
    $("#logs").text(
      JSON.stringify(
        Object.fromEntries(
          Object.entries(displayLogs)
            .sort()
            .reverse()
        ),
        null,
        2
      ).replace(/(?:\\[rn]|[\r\n]+)+/g, "\n")
    );
  }
}

/**
 * Display logs.
 */
function displayLogs() {
  call(`/automation/get_logs/${jobId}`, (logs) => {
    $("#display,#compare_with").empty();
    const times = Object.keys(logs);
    times.forEach((option) => {
      $("#display,#compare_with").append(
        $("<option></option>")
          .attr("value", option)
          .text(option)
      );
    });
    $("#display,#compare_with").val(times[times.length - 1]);
    displayLog(logs);
  });
}

/**
 * Display logs.
 * @param {firstTime} firstTime - First time.
 */
// eslint-disable-next-line
function refreshLogs(firstTime = false) {
  if (firstTime) {
    refresh = !refresh;
    $("#refresh-logs-button").text(
      refresh ? "Stop periodic Refresh" : "Trigger periodic Refresh"
    );
  }
  if (refresh) {
    displayLogs();
    setTimeout(refreshLogs, 5000);
  }
}

/**
 * Show the logs modal for a job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function showLogs(id) {
  jobId = id;
  $("#logs").empty();
  displayLogs();
  $("#logs-modal").modal("show");
}

/**
 * Clear the logs
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function clearLogs() {
  call(`/automation/clear_logs/${jobId}`, () => {
    $("#logs").empty();
    alertify.notify("Logs cleared.", "success", 5);
    $("#logs-modal").modal("hide");
  });
}

/**
 * Detach window
 */
// eslint-disable-next-line
function detachWindow() {
  window
    .open(`/automation/detach_logs/${jobId}`, "Logs", "height=800,width=600")
    .focus();
  $("#logs-modal").modal("hide");
}

$("#display").on("change", function() {
  call(`/automation/get_logs/${jobId}`, (logs) => {
    displayLog(logs);
    $("#compare_with").val($("#display").val());
  });
});

$("#compare_with").on("change", function() {
  $("#logs").empty();
  const v1 = $("#display").val();
  const v2 = $("#compare_with").val();
  call(`/automation/get_diff/${jobId}/${v1}/${v2}`, function(data) {
    $("#logs").append(
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
  });
}
