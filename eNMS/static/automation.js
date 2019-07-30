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
    const options = {
      mode: $(`#view_type-${id}`).val(),
      modes: ["text", "view"],
      onEvent: function(node, event) {
        if (event.type === "click") {
          let path = "";
          if (node.path[0] == "results") {
            for (let i = 0; i < node.path.length; i++) {
              let element = node.path[i];
              if (typeof element === "number") {
                path += `[${element}]`;
              } else {
                path += path.length ? `["${element}"]` : "payload";
              }
            }
            $(`#payload_query-${id}`).val(path).show();
          } else {
            $(`#payload_query-${id}`).hide()
          }
        }
      },
    };
    new JSONEditor(
      document.getElementById(`display_results-${formId}`),
      options,
      parseObject(JSON.parse(JSON.stringify(results)))
    );
  }
}

/**
 * Display result.
 * @param {id} id - Job id.
 * @param {formId} formId - Form ID.
 */
function displayResults(type, id, formId, compare) {
  const url = compare ? "compare" : "get";
  if ($(`#runtime-${id}`).val() || type == "run") {
    fCall(`/${url}_results/${type}/${id}`, `#results-form-${formId}`, (results) => {
      currentResults = results;
      formatResults(results, id, formId, compare);
    });
  } else {
    $(`#display_results-${formId}`).text("No results yet.");
  }
}

/**
 * Display results.
 * @param {id} id - Job id.
 * @param {type} type - Runtime Type.
 */
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
    if (runtimes) {
      if (type == "workflow" || type == "device") {
        updateJobList(type, id, true);
      } else {
        updateDeviceList(type, id, id, true);
      }
    }
  });
}

/**
 * Display results.
 * @param {id} id - Job id.
 * @param {parentId} parentId - Parent ID.
 * @param {boolean} updateBoth - update both device lists.
 */
function updateDeviceList(type, id, parentId, updateBoth) {
  const formId = parentId || id;
  fCall(`/get_device_list/${id}`, `#results-form-${formId}`, (devices) => {
    let ids;
    if (updateBoth) {
      ids = `#device-${formId},#device_compare-${formId}`;
    } else {
      const comp = $(`#compare-${formId}`).is(":checked") ? "_compare" : "";
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
    if (type == "workflow") {
      updateParentDeviceList(type, id, parentId, updateBoth);
    } else {
      displayResults(type, id, formId);
    }
  });
}

function updateParentDeviceList(type, id, parentId, updateBoth) {
  const formId = parentId || id;
  fCall(`/get_workflow_device_list/${id}`, `#results-form-${formId}`, (devices) => {
    let ids;
    if (updateBoth) {
      ids = `#workflow_device-${formId},#workflow_device_compare-${formId}`;
    } else {
      const comp = $(`#compare-${formId}`).is(":checked") ? "_compare" : "";
      ids = `#workflow_device${comp}-${formId}`;
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
    displayResults(type, id, formId);
  });
}

/**
 * Display results.
 * @param {id} id - Job id.
 * @param {type} type - Runtime Type.
 * @param {boolean} updateBoth - update both job lists.
 */
function updateJobList(type, id, updateBoth) {
  fCall(`/get_job_list/${id}`, `#results-form-${id}`, (jobs) => {
    let ids;
    if (updateBoth) {
      ids = `#job-${id},#job_compare-${id}`;
    } else {
      const comp = $(`#compare-${id}`).is(":checked") ? "_compare" : "";
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
    updateDeviceList(type, id, id, updateBoth);
  });
}

/**
 * Show the results modal for a job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function showLogs(id, job) {
  if (!$(`#logs-${id}`).length) {
    jsPanel.create({
      id: `logs-${id}`,
      theme: "dark filled",
      border: "medium",
      headerTitle: `Logs - ${job.name}`,
      position: "center-top 0 58",
      callback: function() {
        refreshLogs(id, job);
      },
      contentSize: "1450 600",
      contentOverflow: "hidden scroll",
      content: `<pre id="log-text-${id}" style="border: 0;\
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
    configureResultsCallbacks(id, type);
    getRuntimes(type, id);
  });
}

/**
 * Configure display & comparison callbacks
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function configureResultsCallbacks(id, type) {
  if (type != "device") {
    $(`#device-${id},#device_compare-${id}`).on("change", function() {
      $(`#compare-${id}`).prop("checked", this.id.includes("compare"));
      displayResults(type, id, id);
    });
  }

  if (type != "run") {
    $(`#runtime-${id},#runtime_compare-${id}`).on("change", function() {
      $(`#compare-${id}`).prop("checked", this.id.includes("compare"));
      if (type != "device") updateDeviceList(type, id);
      if (type != "service") updateJobList(type, id);
    });
  } else {
    updateDeviceList(type, id)
  }

  if (type != "service") {
    $(`#job-${id},#job_compare-${id}`).on("change", function() {
      $(`#compare-${id}`).prop("checked", this.id.includes("compare"));
      updateDeviceList(type, id);
    });
  }

  $(`#view_type-${id}`).on("change", function() {
    displayResults(type, id, id);
  });

  $(`#compare-btn-${id}`).click(function() {
    displayResults(type, id, id, true);
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
function refreshLogs(id, job) {
  call(`/get_job_logs/${job.runtime}`, function(logs) {
    if (logs) {
      $(`#log-text-${id}`).text(logs);
      setTimeout(() => refreshLogs(id, job), 1500);
    } else {
      $(`#logs-${id}`).remove();
      console.log(job.type);
      const jobType = job.type == "Workflow" ? "workflow" : "service";
      console.log(jobType);
      showResultsPanel(id, job.name, jobType);
    }
  });
}

/**
 * Run job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function runJob(type, id, name) {
  fCall(`/run_job`, `#edit-${type}-form-${id}`, function(job) {
    showLogs(id, job);
    alertify.notify(`Job '${job.name}' started.`, "success", 5);
    if (page == "workflow_builder") {
      if (job.type == "Workflow") {
        getWorkflowState(true);
      } else {
        getJobState(id);
      }
    }
    $(`#${type}-${id}`).remove();
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
