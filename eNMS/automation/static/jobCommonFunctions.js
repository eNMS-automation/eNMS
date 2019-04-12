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
function displayResult(results, id) {
  const value = results[$(`#${id}-display`).val()];
  if (!value) return;
  $(`#${id}-results`).text(
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
function displayResults(id) {
  call(`/automation/get_results/${id}`, (results) => {
    $(`#${id}-display,#${id}-compare_with`).empty();
    const times = Object.keys(results);
    times.forEach((option) => {
      $(`#${id}-display,#${id}-compare_with`).append(
        $("<option></option>")
          .attr("value", option)
          .text(option)
      );
    });
    $(`#${id}-display,#${id}-compare_with`).val(times[times.length - 1]);
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
  jsPanel.create({
    border: "medium",
    headerTitle: "Logs",
    position: "center-top 0 58",
    contentSize: "1100 600",
    content: `
      <div class="modal-body">
        <button class="btn btn-default btn-file" onclick="clearResults(${id})" style="width:100%;">
          Clear
        </button>
        <button class="btn btn-default btn-file" onclick="displayResults(${id})" style="width:100%;">
          Refresh
        </button><br><br>
        <label class="control-label col-md-2 col-sm-2 col-xs-12">Display :</label>
        <div class="col-md-10 col-sm-10 col-xs-12">
          <select class="form-control" id="${id}-display" name="display"></select>
        </div>
        <label class="control-label col-md-2 col-sm-2 col-xs-12">Compare With :</label>
        <div class="col-md-10 col-sm-10 col-xs-12">
          <select class="form-control" id="${id}-compare_with" name="compare_with"></select>
        </div>
        <hr><hr><hr><hr>
        <div class="row">
          <div class="col-md-12 col-sm-12 col-xs-12">
          <pre id="${id}-results"></pre>
          </div>
        </div>
      </div>
    `,
    dragit: {
      opacity: 0.7,
      containment: [5, 5, 5, 5],
    },
  });
  configureCallbacks(id);
  displayResults(id);
}

/**
 * Configure display & comparison callbacks
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function configureCallbacks(id) {
  $(`#${id}-display`).on("change", function() {
    call(`/automation/get_results/${id}`, (results) => {
      displayResult(results, id);
      $(`#${id}-compare_with`).val($(`#${id}-display`).val());
    });
  });
  
  $(`#${id}-compare_with`).on("change", function() {
    $(`#${id}-results`).empty();
    const v1 = $(`#${id}-display`).val();
    const v2 = $(`#${id}-compare_with`).val();
    call(`/automation/get_diff/${id}/${v1}/${v2}`, function(data) {
      $(`#${id}-results`).append(
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
  call(`/automation/clear_results/${id}`, () => {
    $(`#${id}-results,#${id}-compare_with,#${id}-display`).empty();
    alertify.notify("Results cleared.", "success", 5);
  });
}

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
