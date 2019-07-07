/*
global
action: false
alertify: false
call: false
editService: false
runJob: false
showLogs: false
showPanel: false
showResultsPanel: false
showTypePanel: false
vis: false
workflow: true
*/

const container = document.getElementById("network");
const dsoptions = {
  edges: {
    font: {
      size: 12,
    },
  },
  nodes: {
    shape: "box",
    font: {
      bold: {
        color: "#0077aa",
      },
    },
  },
  manipulation: {
    enabled: false,
    addNode: function(data, callback) {},
    addEdge: function(data, callback) {
      if (data.from == 2) {
        alertify.notify("You cannot draw an edge from the End.", "error", 5);
      }
      if (data.from != data.to) {
        data.subtype = edgeType;
        saveEdge(data);
      }
    },
  },
};

let nodes;
let edges;
let graph;
let selectedNode;
let edgeType;
let lastModified;

/**
 * Display a workflow.
 * @param {wf} wf - A workflow.
 * @return {graph}
 */
function displayWorkflow(wf) {
  nodes = new vis.DataSet(wf.jobs.map(jobToNode));
  edges = new vis.DataSet(wf.edges.map(edgeToEdge));
  wf.jobs.filter((s) => s.type == "IterationService").map(drawIterationService);
  graph = new vis.Network(container, { nodes: nodes, edges: edges }, dsoptions);
  graph.setOptions({ physics: false });
  graph.on("oncontext", function(properties) {
    properties.event.preventDefault();
    const node = this.getNodeAt(properties.pointer.DOM);
    const edge = this.getEdgeAt(properties.pointer.DOM);
    if (typeof node !== "undefined" && node != 1 && node != 2) {
      graph.selectNodes([node]);
      $(".global,.edge-selection").hide();
      $(".node-selection").show();
      selectedNode = nodes.get(node);
    } else if (typeof edge !== "undefined" && node != 1 && node != 2) {
      graph.selectEdges([edge]);
      $(".global,.node-selection").hide();
      $(".edge-selection").show();
      selectedNode = nodes.get(node);
    } else {
      $(".node-selection").hide();
      $(".global").show();
    }
  });
  graph.on("doubleClick", function(properties) {
    properties.event.preventDefault();
    const node = this.getNodeAt(properties.pointer.DOM);
    if (node) {
      const job = workflow.jobs.find((w) => w.id === node);
      if (job.type == "Workflow") {
        switchToWorkflow(node);
      } else {
        editService(node);
      }
    }
  });
  graph.on("dragEnd", () => savePositions());
  $(`#add_jobs option[value='${wf.id}']`).remove();
  $("#add_jobs").selectpicker("refresh");
  lastModified = wf.last_modified;
  return graph;
}

/**
 * Display a workflow.
 * @param {workflowId} workflowId - Workflow ID.

 */
function switchToWorkflow(workflowId) {
  call(`/get/workflow/${workflowId}`, function(result) {
    workflow = result;
    graph = displayWorkflow(result);
    alertify.notify(`Workflow '${workflow.name}' displayed.`, "success", 5);
  });
}

/**
 * Display "Restart Workflow" panel.
 */
// eslint-disable-next-line
function showRestartPanel(job) {
  showPanel("restart_workflow", job.id, function() {
    call(`/get_job_results/${workflow.id}`, function(results) {
      Object.keys(results).forEach((option) => {
        $(`#payload_version-${job.id}`).append(
          $("<option></option>")
            .attr("value", option)
            .text(option)
        );
      });
      $(`#payload_version-${job.id}`).selectpicker("refresh");
    });
  });
}

/**
 * Restart Workflow.
 */
// eslint-disable-next-line
function restartWorkflow(id) {
  const version = $(`#payload_version-${id}`).val();
  call(`/restart_workflow/${workflow.id}/${id}/${version}`, function(name) {
    alertify.notify(`Workflow '${name}' started.`, "success", 5);
    getWorkflowState();
  });
}

/**
 * Add an existing job to the workflow.
 */
// eslint-disable-next-line
function addJobsToWorkflow(jobs) {
  if (!workflow) {
    alertify.notify(
      `You must create a workflow in the
    'Workflow management' page first.`,
      "error",
      5
    );
  } else {
    jobs = $("#jobs").length
      ? $("#jobs")
          .val()
          .join("-")
      : jobs;
    call(`/add_jobs_to_workflow/${workflow.id}/${jobs}`, function(result) {
      lastModified = result.update_time;
      result.jobs.forEach((job, index) => {
        $("#add_jobs").remove();
        if (graph.findNode(job.id).length == 0) {
          nodes.add(jobToNode(job, index));
          alertify.notify(
            `Job '${job.name}' added to the workflow.`,
            "success",
            5
          );
        } else {
          alertify.notify(
            `${job.type} '${job.name}' already in workflow.`,
            "error",
            5
          );
        }
      });
    });
  }
}

/**
 * Delete job from the workflow (back-end).
 * @param {id} id - Id of the job to be deleted.
 */
function deleteNode(id) {
  call(`/delete_node/${workflow.id}/${id}`, function(result) {
    lastModified = result.update_time;
    alertify.notify(
      `'${result.job.name}' deleted from the workflow.`,
      "success",
      5
    );
  });
}

/**
 * Add edge to the workflow object (back-end).
 * @param {edge} edge - Edge to add to the workflow.
 */
function saveEdge(edge) {
  const param = `${workflow.id}/${edge.subtype}/${edge.from}/${edge.to}`;
  call(`/add_edge/${param}`, function(result) {
    lastModified = result.update_time;
    edges.add(edgeToEdge(result.edge));
    graph.addEdgeMode();
  });
}

/**
 * Delete edge from the workflow (back-end).
 * @param {edgeId} edgeId - Id of the edge to be deleted.
 */
function deleteEdge(edgeId) {
  call(`/delete_edge/${workflow.id}/${edgeId}`, (updateTime) => {
    lastModified = updateTime;
  });
}

/**
 * Convert job object to Vis job node.
 * @param {job} job - Job object.
 * @param {int} index - Stairstep display when adding jobs.
 * @return {visJob}.
 */
function jobToNode(job, index) {
  return {
    id: job.id,
    shape: job.shape,
    color: job.color,
    size: job.size,
    label: job.name,
    type: job.type,
    x: job.positions[workflow.name]
      ? job.positions[workflow.name][0]
      : index
      ? -300
      : 0,
    y: job.positions[workflow.name]
      ? job.positions[workflow.name][1]
      : index
      ? index * 50 - 300
      : 0,
  };
}

/**
 * Draw edge to self for iteration service.
 * @param {service} service - Service object.
 */
function drawIterationService(service) {
  edges.add({
    id: -service.id,
    label: service.iterated_job,
    from: service.id,
    to: service.id,
    color: "black",
    arrows: { to: { enabled: true } },
  });
}

/**
 * Convert edge object to Vis job edge.
 * @param {edge} edge - Edge object.
 * @return {visEdge}.
 */
function edgeToEdge(edge) {
  return {
    id: edge.id,
    label: edge.subtype,
    type: edge.subtype,
    from: edge.source_id,
    to: edge.destination_id,
    smooth: {
      type: "curvedCW",
      roundness:
        edge.subtype == "success" ? 0.1 : edge.subtype == "failure" ? -0.1 : 0,
    },
    color: {
      color:
        edge.subtype == "success"
          ? "green"
          : edge.subtype == "failure"
          ? "red"
          : "blue",
    },
    arrows: { to: { enabled: true } },
  };
}

/**
 * Delete selected nodes and edges.
 */
function deleteSelection() {
  const node = graph.getSelectedNodes()[0];
  if (node != 1 && node != 2) {
    if (node) {
      deleteNode(node);
    }
    graph.getSelectedEdges().map((edge) => deleteEdge(edge));
    graph.deleteSelected();
  } else {
    alertify.notify("Start and End cannot be deleted", "error", 5);
  }
}

/**
 * Change the mode (motion, creation of success or failure edge).
 * @param {mode} mode - Mode to switch to.
 */
function switchMode(mode) {
  if (["success", "failure", "prerequisite"].includes(mode)) {
    edgeType = mode;
    graph.addEdgeMode();
    alertify.notify(`Mode: creation of ${mode} edge.`, "success", 5);
  } else {
    graph.addNodeMode();
    alertify.notify("Mode: node motion.", "success", 5);
  }
  $(".dropdown-submenu a.menu-layer")
    .next("ul")
    .toggle();
}

$("#current-workflow").on("change", function() {
  $("#add_jobs").append(
    `<option value='${workflow.id}'>${workflow.name}</option>`
  );
  switchToWorkflow(this.value);
});

/**
 * Save positions of the workflow nodes.
 */
function savePositions() {
  $.ajax({
    type: "POST",
    url: `/save_positions/${workflow.id}`,
    dataType: "json",
    contentType: "application/json;charset=UTF-8",
    data: JSON.stringify(graph.getPositions(), null, "\t"),
    success: function(updateTime) {
      if (updateTime) {
        lastModified = updateTime;
      } else {
        alertify.notify("HTTP Error 403 – Forbidden", "error", 5);
      }
    },
  });
}

Object.assign(action, {
  "Run Workflow": runWorkflow,
  Edit: (job) => showTypePanel(job.type, job.id),
  Run: (job) => runJob(job.id),
  Results: (job) => showResultsPanel(job.id, job.label),
  "Restart Workflow": (job) => showRestartPanel(job),
  "Create Workflow": () => showTypePanel("workflow"),
  "Edit Workflow": () => showTypePanel("workflow", workflow.id),
  "Workflow Results": () => showResultsPanel(workflow.id, workflow.name, true),
  "Workflow Logs": () => showLogs(workflow.id),
  "Add to Workflow": () => showPanel("add_jobs"),
  "Remove from Workflow": deleteSelection,
  "Create 'Success' edge": () => switchMode("success"),
  "Create 'Failure' edge": () => switchMode("failure"),
  "Create 'Prerequisite' edge": () => switchMode("prerequisite"),
  "Move Nodes": () => switchMode("node"),
});

$("#network").contextMenu({
  menuSelector: "#contextMenu",
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selectedNode);
  },
});

/**
 * Start the workflow.
 */
function runWorkflow() {
  workflow.jobs.forEach((job) => colorJob(job.id, job.color));
  runJob(workflow.id);
}

/**
 * Get Workflow State.
 * @param {id} id - Workflow Id.
 * @param {color} color - Node color.
 */
function colorJob(id, color) {
  nodes.update({ id: id, color: color });
}

/**
 * Get Job State.
 * @param {id} id - Job Id.
 */
// eslint-disable-next-line
function getJobState(id) {
  call(`/get/service/${id}`, function(service) {
    if (service.is_running) {
      colorJob(id, "#89CFF0");
      $("#status").text("Status: Running.");
      $("#current-job").text(`Current job: ${service.name}.`);
      setTimeout(() => getJobState(id), 1500);
    } else {
      $("#status").text("Status: Idle.");
      $("#current-job").empty();
      colorJob(id, service.color);
    }
  });
}

/**
 * Get Workflow State.
 */
function getWorkflowState() {
  if (workflow && workflow.id) {
    call(`/get/workflow/${workflow.id}`, function(wf) {
      if (wf.last_modified !== lastModified) {
        displayWorkflow(wf);
      }
      $("#status").text(`Status: ${wf.is_running ? "Running" : "Idle"}.`);
      if (wf.id == workflow.id) {
        if (Object.keys(wf.state).length !== 0) {
          if (wf.state.current_device) {
            $("#current-device").text(
              `Current device: ${wf.state.current_device}.`
            );
          }
          if (wf.state.current_job) {
            colorJob(wf.state.current_job.id, "#89CFF0");
            $("#current-job").text(
              `Current job: ${wf.state.current_job.name}.`
            );
          } else {
            $("#current-device,#current-job").empty();
          }
          if (wf.state.jobs) {
            $.each(wf.state.jobs, (id, success) => {
              colorJob(id, success ? "#32cd32" : "#FF6666");
            });
          }
        } else {
          $("#current-device,#current-job").empty();
          wf.jobs.forEach((job) => colorJob(job.id, job.color));
        }
        setTimeout(getWorkflowState, wf.is_running ? 700 : 15000);
      }
    });
  }
}

(function() {
  call("/get_all/workflow", function(workflows) {
    workflows.sort((a, b) => a.name.localeCompare(b.name));
    for (let i = 0; i < workflows.length; i++) {
      $("#current-workflow").append(
        `<option value="${workflows[i].id}">${workflows[i].name}</option>`
      );
    }
    if (workflow) {
      $("#current-workflow").val(workflow.id);
      displayWorkflow(workflow);
    } else {
      workflow = $("#current-workflow").val();
      if (workflow) {
        switchToWorkflow(workflow);
      } else {
        alertify.notify(
          `You must create a workflow in the
        'Workflow management' page first.`,
          "error",
          5
        );
      }
    }
    $("#current-workflow").selectpicker({
      liveSearch: true,
    });
  });
  getWorkflowState();
})();
