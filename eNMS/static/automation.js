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
function workflowRunMode(instance) {
  call(`/get_runtimes/workflow/${instance.id}`, function(runtimes) {
    instance.jobs.forEach((job) => {
      $(`#workflow-payloads_to_exclude-${instance.id}`).append(
        $("<option></option>")
          .attr("value", job.name)
          .text(job.name)
      );
    });
    runtimes.forEach((runtime) => {
      $(`#workflow-payload_version-${instance.id}`).append(
        $("<option></option>")
          .attr("value", runtime[0])
          .text(runtime[0])
      );
    });
    $(`#workflow-payload_version-${instance.id}`).val(
      runtimes[runtimes.length - 1]
    );
    $(`#workflow-payload_version-${instance.id}`).selectpicker("refresh");
    $(`#workflow-payloads_to_exclude-${instance.id}`).selectpicker("refresh");
  });
}

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
    const options = {
      mode: $(`#view_type-${id}`).val(),
      modes: ["text", "view"],
    };
    new JSONEditor(
      document.getElementById(`display_results-${formId}`),
      options,
      parseObject(JSON.parse(JSON.stringify(results)))
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
    if (runtimes) {
      if (type == "workflow" || type == "device") {
        updateJobList(type, id, true);
      } else {
        updateDeviceLists(type, id, id, true, true);
      }
    }
  });
}

function updateDeviceLists(type, id, parentId, updateBoth, workflowDevice) {
  const workflow = workflowDevice ? "workflow_" : "";
  const formId = parentId || id;
  fCall(
    `/get_${workflow}device_list/${id}`,
    `#results-form-${formId}`,
    (result) => {
      if (workflowDevice && result.workflow_devices.length) {
        updateDeviceList(
          formId,
          updateBoth,
          "workflow_",
          result.workflow_devices
        );
        $(`#workflow_device-row-${id}`).show();
      } else {
        if (workflowDevice) {
          $(`#workflow_device-row-${id}`).hide();
          emptyDeviceList(formId, updateBoth, "workflow_");
        }
        updateDeviceList(
          formId,
          updateBoth,
          "",
          workflowDevice ? result.devices : result
        );
      }
      displayResults(type, id, formId);
    }
  );
}

function emptyDeviceList(formId, updateBoth, workflow) {
  let ids;
  if (updateBoth) {
    ids = `#${workflow}device-${formId},#${workflow}device_compare-${formId}`;
  } else {
    const comp = $(`#compare-${formId}`).is(":checked") ? "_compare" : "";
    ids = `#${workflow}device${comp}-${formId}`;
  }
  $(ids).empty();
}

function updateDeviceList(formId, updateBoth, workflow, devices) {
  if (!devices.length) return;
  let ids;
  if (updateBoth) {
    ids = `#${workflow}device-${formId},#${workflow}device_compare-${formId}`;
  } else {
    const comp = $(`#compare-${formId}`).is(":checked") ? "_compare" : "";
    ids = `#${workflow}device${comp}-${formId}`;
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
}

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
    $(ids).val(id);
    $(ids).selectpicker("refresh");
    updateDeviceLists(type, id, id, updateBoth, true);
  });
}

// eslint-disable-next-line
function showResultsPanel(id, name, type, runtime) {
  createPanel(`${type}_results`, `Results - ${name}`, id, function() {
    configureResultsCallbacks(id, type);
    if (runtime) {
      $(`#runtime-${id},#runtime_compare-${id}`).append(
        $("<option></option>")
          .attr("value", runtime)
          .text(runtime)
      );
      $(`#runtime-row-${id}`).hide();
      if (type == "workflow") {
        updateJobList(type, id, true);
      } else {
        updateDeviceLists(type, id, id, true, true);
      }
    } else {
      getRuntimes(type, id);
    }
  });
}

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
      if (type == "workflow") updateDeviceLists(type, id, id, false, true);
      if (type == "service") updateDeviceLists(type, id);
      if (type != "service") updateJobList(type, id);
    });
  }

  if (type != "service") {
    $(`#job-${id},#job_compare-${id}`).on("change", function() {
      $(`#compare-${id}`).prop("checked", this.id.includes("compare"));
      updateDeviceLists(type, id, id, false, true);
    });
  }

  $(`#workflow_device-${id},#workflow_device_compare-${id}`).on(
    "change",
    function() {
      $(`#compare-${id}`).prop("checked", this.id.includes("compare"));
      updateDeviceLists(type, id);
    }
  );

  $(`#view_type-${id}`).on("change", function() {
    displayResults(type, id, id);
  });

  $(`#compare-btn-${id}`).click(function() {
    displayResults(type, id, id, true);
  });

  if (type == "run" || type == "service") {
    updateDeviceLists(type, id, id);
  }
}

// eslint-disable-next-line
function clearResults(id) {
  call(`/clear_results/${id}`, () => {
    alertify.notify("Results cleared.", "success", 5);
    $(`#results-${id}`).remove();
  });
}

// eslint-disable-next-line
function refreshLogs(runtime, jobId, jobType, jobName, first) {
  const runtimeId = runtime.toString().replace(/[.:-\s]/g, "");
  call(`/get_job_logs/${runtime}`, function(result) {
    $(`#log-text-${runtimeId}`).text(result.logs);
    if (result.refresh) {
      setTimeout(() => refreshLogs(runtime, jobId, jobType), 1500);
    } else if (!first) {
      $(`#logs-${runtimeId}`).remove();
      jobType = jobType == "Workflow" ? "workflow" : "service";
      showResultsPanel(jobId, jobName, jobType, runtime);
    }
  });
}

// eslint-disable-next-line
function showLogs(runtime, jobId, jobType, jobName) {
  const runtimeId = runtime.toString().replace(/[.:-\s]/g, "");
  if (!$(`#logs-${runtimeId}`).length) {
    jsPanel.create({
      id: `logs-${runtimeId}`,
      theme: "dark filled",
      border: "medium",
      headerTitle: `Logs - ${jobName}`,
      position: "center-top 0 58",
      callback: function() {
        refreshLogs(runtime, jobId, jobType, jobName, true);
      },
      contentSize: "1450 600",
      contentOverflow: "hidden scroll",
      content: `<pre id="log-text-${runtimeId}" style="border: 0;\
        background-color: transparent; color: white;"></pre>`,
      dragit: {
        opacity: 0.7,
        containment: [5, 5, 5, 5],
      },
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
    runLogic(job);
  });
}

function runLogic(job) {
  showLogs(job.runtime, job.id, job.type, job.name);
  alertify.notify(`Job '${job.name}' started.`, "success", 5);
  if (page == "workflow_builder") {
    if (job.type == "Workflow") {
      $("#current-runtimes").append(
        `<option value='${job.runtime}'>${job.runtime}</option>`
      );
      $("#current-runtimes").val(job.runtime);
      $("#current-runtimes").selectpicker("refresh");
      getWorkflowState(true);
    } else {
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
