/*
global
alertify: false
call: false
diffview: false
editService: false
getJobState: false
getWorkflowState: false
jsPanel: false
showTypePanel: false
*/

let refreshJob = {};

/**
 * Display custom form.
 * @param {id} id - Service ID.
 */
// eslint-disable-next-line
function displayCustomForm(id) {
  call(`/get_service/${id || $("#service-type").val()}`, function(customForm) {
    for (const type of ["boolean", "list"]) {
      const fields = $(`#${id}-service-${type}_fields`);
      const prop = type == "boolean" ? customForm.boolean_properties : customForm.list_properties;
      fields.val(`${fields.val()},${prop}`);
    }
    $(id ? `#${id}-service-custom-form` : "#service-custom-form").html(customForm.html);
    if (customForm.service) processInstance("service", customForm.service);
  });
}

/**
 * Custom code upon opening panel.
 * @param {type} type - Service or Workflow.
 */
// eslint-disable-next-line
function panelCode(type, id) {
  console.log($(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).length);
  $(id ? `#${id}-${type}-wizard` : `#${type}-wizard`).smartWizard({
    enableAllSteps: true,
    keyNavigation: false,
    transitionEffect: "none",
  });
  $(".buttonFinish,.buttonNext,.buttonPrevious").hide();
  if (type == "service") {
    for (let i = 0; i < servicesClasses.length; i++) {
      $("#service-type").append(
        `<option value='${servicesClasses[i]}'>${servicesClasses[i]}</option>`
      );
    }
    if (id) {
      $(`#${id}-service-type`).prop("disabled", true);
    } else {
      $("#service-type").change(function() {
        displayCustomForm();
      });
    }
    displayCustomForm(id);
  }
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

/**
 * Display result.
 * @param {results} results - Results.
 * @param {id} id - Job id.
 */
function displayResult(results, id) {
  const value = results[$(`#display-${id}`).val()];
  if (!value) return;
  $(`#results-${id}`).text(
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
 * @param {id} id - Job id.
 */
function displayResults(id) {
  call(`/get_results/${id}`, (results) => {
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
  createPanel(
    `results-panel-${id}`,
    "1000 600",
    "../results_form",
    function(panel) {
      panel.content.innerHTML = this.responseText;
      panel.setHeaderTitle("Job results");
      $("#display").prop("id", `display-${id}`);
      $("#compare_with").prop("id", `compare_with-${id}`);
      $("#results").prop("id", `results-${id}`);
      configureCallbacks(id);
      displayResults(id);
    }
  );
}

/**
 * Configure display & comparison callbacks
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function configureCallbacks(id) {
  $(`#display-${id}`).on("change", function() {
    call(`/get_results/${id}`, (results) => {
      displayResult(results, id);
      $(`#compare_with-${id}`).val($(`#display-${id}`).val());
    });
  });

  $(`#compare_with-${id}`).on("change", function() {
    $(`#results-${id}`).empty();
    const v1 = $(`#display-${id}`).val();
    const v2 = $(`#compare_with-${id}`).val();
    call(`/get_diff/${id}/${v1}/${v2}`, function(data) {
      $(`#results-${id}`).append(
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
    $(`#results-${id},#compare_with-${id},#display-${id}`).empty();
    alertify.notify("Results cleared.", "success", 5);
  });
}

/**
 * Run job.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function runJob(id) {
  call(`/run_job/${id}`, function(job) {
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
  fCall(
    `/automation/duplicate_workflow/${id}`,
    "#edit-workflow-form",
    (workflow) => {
      table.ajax.reload(null, false);
      alertify.notify("Workflow successfully duplicated", "success", 5);
    }
  );
}
