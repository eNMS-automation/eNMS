/*
global
addJobsToWorkflow: false
alertify: false
call: false
createPanel: false
diffview: false
displayWorkflow: false
fCall: false
getJobState: false
getWorkflowState: false
JSONEditor: false
jsPanel: false
nodes: true
page: false
showTypePanel: false
table: false
workflow: true
*/

let currentResults = {};

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
function saveService(service, id) {
  if (page == "workflow_builder") {
    if (id) {
      nodes.update({ id: id, label: service.name });
    } else {
      addJobsToWorkflow([service.id]);
    }
  }
}

/**
 * Save a service.
 * @param {service} service - Service instance.
 */
// eslint-disable-next-line
function copyResultsToClipboard(id) {
  $(`#display-text-${id}`).prop("checked", true);
  displayResults(id, id);
  let node = document.getElementById(`display_results-${id}`);
  if (document.body.createTextRange) {
    const range = document.body.createTextRange();
    range.moveToElementText(node);
    range.select();
  } else if (window.getSelection) {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(node);
    selection.removeAllRanges();
    selection.addRange(range);
  } else {
    alertify.notify("Selection not supported by your browser", "error", 5);
  }
  document.execCommand("copy");
}

/**
 * Save a workflow.
 * @param {workflow object} workflow - Workflow instance.
 */
// eslint-disable-next-line
function saveWorkflow(newWorkflow) {
  if (page == "workflow_builder") {
    $("#current-workflow").append(
      `<option value="${newWorkflow.id}">${newWorkflow.name}</option>`
    );
    $("#current-workflow").val(newWorkflow.id);
    $("#current-workflow").selectpicker("refresh");
    workflow = newWorkflow;
    displayWorkflow(workflow);
  }
}

/**
 * Parse object to break strings into list for JSON display.
 * @param {obj} obj - Object.
 * @return {obj}.
 */
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

/**
 * Format results.
 * @param {results} results - Results.
 * @param {id} id - Job id.
 * @param {id} formId - Form ID.
 */
function formatResults(results, id, formId) {
  if (!results) results = currentResults;
  if (!results) {
    $(`#display_results-${formId}`).text("No results yet.");
  } else if ($(`#view_type-${id}`).val() == "compare") {
    $(`#display_results-${formId}`).empty();
    $(`#display_results-${formId}`).append(
      diffview.buildView({
        baseTextLines: results.first,
        newTextLines: results.second,
        opcodes: results.opcodes,
        baseTextName: $(`#timestamp-${id}`).val(),
        newTextName: $(`#timestamp_compare-${id}`).val(),
        contextSize: null,
        viewType: 0,
      })
    );
  } else if ($(`#view_type-${id}`).val() == "json") {
    $(`#display_results-${formId}`).empty();
    new JSONEditor(
      document.getElementById(`display_results-${formId}`),
      { mode: "view" },
      parseObject(JSON.parse(JSON.stringify(results)))
    );
  } else {
    $(`#display_results-${formId}`).html(
      `<pre>${JSON.stringify(results, null, 2)
        .replace(/(?:\\[rn]|[\r\n]+)+/g, "\n")
        .replace(/\\"/g, `"`)
        .replace(/\\\\/g, "\\")}</pre>`
    );
  }
}

/**
 * Display result.
 * @param {id} id - Job id.
 * @param {formId} formId - Form ID.
 */
function displayResults(id, formId) {
  const url = $(`#view_type-${id}`).val() == "compare" ? "compare" : "get";
  fCall(`/${url}_job_results/${id}`, `#results-form-${formId}`, (results) => {
    currentResults = results;
    formatResults(results, id, formId);
  });
}

/**
 * Display results.
 * @param {id} id - Job id.
 * @param {type} type - Timestamp Type.
 */
function getTimestamps(id, type) {
  call(`/get_timestamps/${type}/${id}`, (timestamps) => {
    $(`#timestamp-${id},#timestamp_compare-${id}`).empty();
    timestamps.forEach((timestamp) => {
      $(`#timestamp-${id},#timestamp_compare-${id}`).append(
        $("<option></option>")
          .attr("value", timestamp[0])
          .text(timestamp[1])
      );
    });
    const mostRecent = timestamps[timestamps.length - 1];
    $(`#timestamp-${id},#timestamp_compare-${id}`).val(mostRecent);
    $(`#timestamp-${id},#timestamp_compare-${id}`).selectpicker("refresh");
    if (timestamps) {
      updateDeviceList(id, id, true);
      if (type == "workflow" || type == "device") updateJobList(id, type, true);
    }
  });
}

/**
 * Display results.
 * @param {id} id - Job id.
 * @param {parentId} parentId - Parent ID.
 */
function updateDeviceList(id, parentId, updateBoth) {
  const formId = parentId || id;
  fCall(
    `/get_device_list/${id}`,
    `#results-form-${formId}`,
    (devices) => {
      if (updateBoth) {
        ids = `#device-${formId},#device_compare-${formId}`;
      } else {
        comp = $(`#compare-${formId}`).is(':checked') ? "_compare" : "";
        ids = `#device${comp}-${formId}`;
      }
      $(ids).empty();
      devices.forEach((device) => {
        $(ids).append(
          $("<option></option>")
            .attr("value", device[0])
            .text(device[1])
        );
      });
      $(ids).selectpicker("refresh");
      displayResults(id, formId);
    }
  );
}

/**
 * Display results.
 * @param {id} id - Job id.
 * @param {type} type - Timestamp Type.
 */
function updateJobList(id, type, updateBoth) {
  fCall(`/get_job_list/${type}/${id}`, `#results-form-${id}`, (jobs) => {
    if (updateBoth) {
      ids = `#job-${id},#job_compare-${id}`;
    } else {
      comp = $(`#compare-${id}`).is(':checked') ? "_compare" : "";
      ids = `#job${comp}-${id}`;
    }
    $(ids).empty();
    jobs.forEach((job) => {
      $(ids).append(
        $("<option></option>")
          .attr("value", job[0])
          .text(job[1])
      );
    });
    $(ids).selectpicker("refresh");
    displayResults(id, id);
  });
}

/**
 * Show the results modal for a job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function showLogs(id, name) {
  if (!$(`#logs-${id}`).length) {
    jsPanel.create({
      theme: "dark filled",
      border: "medium",
      headerTitle: `Logs - ${name}`,
      position: "center-top 0 58",
      contentSize: "1450 600",
      contentOverflow: "hidden scroll",
      content: `<pre id="logs-${id}" style="border: 0;\
        background-color: transparent; color: white;"></pre>`,
      dragit: {
        opacity: 0.7,
        containment: [5, 5, 5, 5],
      },
    });
  }
}

/**
 * Show the results modal for a job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function showResultsPanel(id, name, type) {
  createPanel(`${type}_results`, `Results - ${name}`, id, function() {
    configureCallbacks(id, type);
    getTimestamps(id, type);
  });
}

/**
 * Configure display & comparison callbacks
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function configureCallbacks(id, type) {
  if (type != "device") {
    $(`#device-${id},#device_compare-${id}`).on("change", function() {
      $(`#compare-${id}`).prop('checked', this.id.includes("compare"));
      displayResults(id, id);
    });
  }

  $(`#timestamp-${id},#timestamp_compare-${id}`).on("change", function() {
    $(`#compare-${id}`).prop('checked', this.id.includes("compare"));
    if (type != "device") updateDeviceList(id);
    if (type != "service") updateJobList(id, type);
  });

  if (type != "service") {
    $(`#job-${id},#job_compare-${id}`).on("change", function() {
      $(`#compare-${id}`).prop('checked', this.id.includes("compare"));
      displayResults(id, id);
    });
  }

  $(`#view_type-${id},#success_type-${id}`).on("change", function() {
    displayResults(id, id);
  });
}

/**
 * Clear the results
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function clearResults(id) {
  call(`/clear_results/${id}`, () => {
    alertify.notify("Results cleared.", "success", 5);
    $(`#results-${id}`).remove();
  });
}

/**
 * Refresh the logs
 * @param {id} id - Job ID.
 */
// eslint-disable-next-line
function refreshLogs(id, name) {
  let xhr = new XMLHttpRequest();
  xhr.open("GET", `/stream_logs/${name}`, true);
  xhr.send(null);

  /**
   * Handle real-time logs data.
   */
  function handleNewData() {
    let messages = xhr.responseText.split("\n");
    messages.slice(position, -1).forEach(function(value) {
      $(`#logs-${id}`).append(`${value}<br>`);
    });
    position = messages.length - 1;
  }

  let position = 0;
  let timer;
  timer = setInterval(function() {
    handleNewData();
    if (xhr.readyState == XMLHttpRequest.DONE) {
      clearInterval(timer);
    }
  }, 1000);
}

/**
 * Run job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function runJob(id, name) {
  showLogs(id, name);
  refreshLogs(id, name);
  call(`/run_job/${id}`, function(job) {
    alertify.notify(`Job '${job.name}' started.`, "success", 5);
    if (page == "workflow_builder") {
      if (job.type == "Workflow") {
        getWorkflowState();
      } else {
        getJobState(id);
      }
    }
  });
}

/**
 * Show Log History.
 * @param {name} name - Job name.
 */
// eslint-disable-next-line
function showLogHistory(id, name) {
  call(`/get_job_logs/${name}`, function(result) {
    showLogs(id, name);
    $(`#logs-${id}`).empty();
    result.forEach((line) => $(`#logs-${id}`).append(line));
  });
}

/**
 * Display instance modal for editing.
 * @param {id} id - Instance ID.
 */
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

/**
 * Export a job.
 * @param {int} id - Job ID.
 */
// eslint-disable-next-line
function exportJob(id) {
  call(`/export_job/${id}`, () => {
    alertify.notify("Export successful.", "success", 5);
  });
}

/**
 * Pause a task.
 * @param {id} id - Task id.
 */
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

/**
 * Resume a task.
 * @param {id} id - Task id.
 */
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
