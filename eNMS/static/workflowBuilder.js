/*
global
action: false
alertify: false
call: false
createPanel: false
fCall: false
normalRun: false
runLogic: false
showLogsPanel: false
showPanel: false
showResultsPanel: false
showTypePanel: false
vis: false
workflow: true
workflowRunMode: false
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
  interaction: {
    hover: true,
    hoverConnectedEdges: false,
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
let stateUpdate = false;
let hoveredLabel;
let mousePosition;

function displayWorkflow(workflowData) {
  workflow = workflowData.workflow;
  nodes = new vis.DataSet(workflow.jobs.map(jobToNode));
  edges = new vis.DataSet(workflow.edges.map(edgeToEdge));
  workflow.jobs
    .filter((s) => s.type == "IterationService")
    .map(drawIterationService);
  workflow.jobs.filter((s) => s.iteration_values != "").map(drawIterationEdge);
  for (const [content, position] of Object.entries(workflow.labels)) {
    drawLabel(content, position);
  }
  graph = new vis.Network(container, { nodes: nodes, edges: edges }, dsoptions);
  graph.setOptions({ physics: false });
  graph.on("oncontext", function(properties) {
    mousePosition = graph.DOMtoCanvas({"x": properties.event.offsetX, "y": properties.event.offsetY});
    properties.event.preventDefault();
    const node = this.getNodeAt(properties.pointer.DOM);
    const edge = this.getEdgeAt(properties.pointer.DOM);
    if (typeof node !== "undefined" && node != 1 && node != 2) {
      graph.selectNodes([node]);
      $(".global,.edge-selection").hide();
      $(`.${node[0] === "L" ? "label" : "node"}-selection`).show();
      $(`.${node[0] === "L" ? "node" : "label"}-selection`).hide();
      selectedNode = nodes.get(node);
    } else if (typeof edge !== "undefined" && node != 1 && node != 2) {
      graph.selectEdges([edge]);
      $(".global,.node-selection,.label-selection").hide();
      $(".edge-selection").show();
      selectedNode = nodes.get(node);
    } else {
      $(".node-selection,.label-selection").hide();
      $(".global").show();
    }
  });
  graph.on("doubleClick", function(properties) {
    properties.event.preventDefault();
    let node = this.getNodeAt(properties.pointer.DOM);
    if (node) {
      node = parseInt(node);
      const job = workflow.jobs.find((w) => w.id === node);
      if (job.type == "Workflow") {
        switchToWorkflow(node);
        $("#current-workflow").val(node);
        $("#current-workflow").selectpicker("refresh");
      } else {
        showTypePanel(job.type, job.id);
      }
    }
  });
  $("#current-runtimes").empty();
  $("#current-runtimes").append("<option value=''>Normal Display</option>");
  workflowData.runtimes.forEach((runtime) => {
    $("#current-runtimes").append(
      `<option value='${runtime}'>${runtime}</option>`
    );
  });
  $("#current-runtimes").val("");
  $("#current-runtimes").selectpicker("refresh");
  graph.on("dragEnd", () => savePositions());
  $(`#add_jobs option[value='${workflow.id}']`).remove();
  $("#add_jobs").selectpicker("refresh");
  lastModified = workflow.last_modified;

  return graph;
}

function switchToWorkflow(workflowId) {
  call(`/get_workflow_state/${workflowId}`, function(result) {
    workflow = result.workflow;
    graph = displayWorkflow(result);
    if (!stateUpdate) getWorkflowState(true);
    alertify.notify(`Workflow '${workflow.name}' displayed.`, "success", 5);
  });
}

// eslint-disable-next-line
function saveWorkflowJob(job, update, index) {
  if (page == "workflow_builder") {
    if (update) {
      nodes.update(jobToNode(job));
      var jobIndex = workflow.jobs.findIndex(job => job.id == job.id);
      workflow.jobs[jobIndex] = job;
    } else {
      addJobsToWorkflow([job.id])
    }
    if (job.iteration_values != "") {
      drawIterationEdge(job);
    } else {
      edges.remove(-job.id);
    }
  }
}

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
          workflow.jobs.push(job);
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

function deleteNode(id) {
  workflow.jobs = workflow.jobs.filter((n) => n.id != id);
  call(`/delete_node/${workflow.id}/${id}`, function(result) {
    lastModified = result.update_time;
    alertify.notify(
      `'${result.job.name}' deleted from the workflow.`,
      "success",
      5
    );
  });
}

function deleteLabel(label) {
  nodes.remove(label.id);
  call(`/delete_label/${workflow.id}/${label.label}`, function(updateTime) {
    delete workflow.labels[label.id];
    lastModified = updateTime;
    alertify.notify("Label removed.", "success", 5);
  });
}

function saveEdge(edge) {
  const param = `${workflow.id}/${edge.subtype}/${edge.from}/${edge.to}`;
  call(`/add_edge/${param}`, function(result) {
    lastModified = result.update_time;
    edges.add(edgeToEdge(result.edge));
    graph.addEdgeMode();
  });
}

function deleteEdge(edgeId) {
  call(`/delete_edge/${workflow.id}/${edgeId}`, (updateTime) => {
    lastModified = updateTime;
  });
}

function formatJobTitle(job) {
  return `
    <b>Type</b>: ${job.type}<br>
    <b>Name</b>: ${job.name}
  `
}

function jobToNode(job, index) {
  return {
    id: job.id,
    shape: job.shape,
    color: job.color,
    size: job.size,
    label: job.name,
    name: job.name,
    type: job.type,
    title: formatJobTitle(job),
    x: job.positions[workflow.name]
      ? job.positions[workflow.name][0]
      : index
      ? index * 50 - 50
      : 0,
    y: job.positions[workflow.name]
      ? job.positions[workflow.name][1]
      : index
      ? index * 50 - 200
      : 0,
  };
}

function drawLabel(content, positions) {
  console.log(content, positions);
  nodes.add({
    id: `L-${content}`,
    shape: "box",
    type: "label",
    label: content,
    borderWidth: 0,
    color: "#FFFFFF",
    x: positions[0],
    y: positions[1],
  });
}

function drawIterationEdge(service) {
  if (!edges.get(-service.id)) {
    edges.add({
      id: -service.id,
      label: "Iteration",
      from: service.id,
      to: service.id,
      color: "black",
      arrows: { to: { enabled: true } },
    });
  }
}

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

$("#current-runtimes").on("change", function() {
  resetDisplay();
  if (!stateUpdate) getWorkflowState(true);
});

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
  Edit: (job) => showTypePanel(job.type, job.id),
  Run: (job) => normalRun(job.id),
  "Run with Updates": (job) => showTypePanel(job.type, job.id, "run"),
  "Run Workflow": () => runWorkflow(),
  "Run Workflow with Updates": () => runWorkflow(true),
  Results: (job) => showResultsPanel(job.id, job.label, "service"),
  "Create Workflow": () => showTypePanel("workflow"),
  "Edit Workflow": () => showTypePanel("workflow", workflow.id),
  "Restart Workflow from Here": (job) =>
    showRestartWorkflowPanel(workflow, job),
  "Workflow Results": () =>
    showResultsPanel(workflow.id, workflow.name, "workflow"),
  "Workflow Logs": () => showLogsPanel(workflow),
  "Add to Workflow": () => showPanel("add_jobs"),
  "Remove from Workflow": deleteSelection,
  "Create 'Success' edge": () => switchMode("success"),
  "Create 'Failure' edge": () => switchMode("failure"),
  "Create 'Prerequisite' edge": () => switchMode("prerequisite"),
  "Move Nodes": () => switchMode("node"),
  "Create Label": () => showPanel("workflow_label"),
  "Edit Label": () => showPanel("workflow_label"),
  "Delete Label": deleteLabel,
});

// eslint-disable-next-line
function createLabel() {
  const params = `${workflow.id}/${mousePosition.x}/${mousePosition.y}`;
  fCall(`/create_label/${params}`, `#workflow_label-form`, function(result) {
    $("#workflow_label").remove();
    drawLabel(result.content, result.positions);
    alertify.notify("Label created.", "success", 5);
  });
}

$("#network").contextMenu({
  menuSelector: "#contextMenu",
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selectedNode);
  },
});

function runWorkflow(withUpdates) {
  workflow.jobs.forEach((job) => colorJob(job.id, job.color));
  if (withUpdates) {
    showTypePanel("Workflow", workflow.id, "run");
  } else {
    normalRun(workflow.id);
  }
}

function showRestartWorkflowPanel(workflow, job) {
  createPanel(
    "restart_workflow",
    `Restart Workflow '${workflow.name}' from '${job.name}'`,
    workflow.id,
    function() {
      $("#start_jobs").val(job.id);
      $("#start_jobs").selectpicker("refresh");
      workflowRunMode(workflow, true);
    }
  );
}

// eslint-disable-next-line
function restartWorkflow() {
  fCall(`/run_job/${workflow.id}`, `#restart_workflow-form`, function(result) {
    $(`#restart_workflow-${workflow.id}`).remove();
    runLogic(result);
  });
}

function colorJob(id, color) {
  nodes.update({ id: id, color: color });
}

// eslint-disable-next-line
function getJobState(id) {
  call(`/get/service/${id}`, function(service) {
    if (service.status == "Running") {
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

// eslint-disable-next-line
function displayWorkflowState(result) {
  if (!result.state) {
    $("#progressbar").hide();
    result.workflow.jobs.forEach((job) => {
      colorJob(job.id, job.color);
    });
  } else {
    $("#progressbar").show();
    $("#progress-success").width(
      `${(result.state.progress.passed * 100) / result.state.progress_max}%`
    );
    $("#progress-failure").width(
      `${(result.state.progress.failed * 100) / result.state.progress_max}%`
    );
    $("#progress-success-span").text(result.state.progress.passed);
    $("#progress-failure-span").text(result.state.progress.failed);
    $("#status").text(`Status: ${result.state.status}`);
    const currJob = result.state.current_job;
    if (currJob) {
      colorJob(currJob.id, "#89CFF0");
      $("#current-job").text(`Current job: ${result.state.current_job.name}.`);
    } else {
      $("#current-job").empty();
    }
    if (result.state.jobs) {
      $.each(result.state.jobs, (id, state) => {
        const color = {
          true: "#32cd32",
          false: "#FF6666",
          skipped: "#D3D3D3",
        };
        if (id in nodes._data) {
          let updateNode = { id: id, color: color[state.success] };
          if (state.type != "Workflow" && state.number_of_targets) {
            let progress = `${state.completed}/${state.number_of_targets}`;
            if (state.failed > 0) progress += ` (${state.failed} failed)`;
            updateNode.label = `${nodes.get(id).name}\n${progress}`;
          }
          nodes.update(updateNode);
        }
      });
    }
    if (result.state.edges) {
      $.each(result.state.edges, (id, devices) => {
        const label = devices == 1 ? "DEVICE" : "DEVICES";
        edges.update({
          id: id,
          label: `<b>${devices} ${label}</b>`,
          font: { size: 15, multi: "html" },
        });
      });
    }
  }
}

function resetDisplay() {
  workflow.jobs.forEach((job) => {
    colorJob(job.id, job.color);
  });
  workflow.edges.forEach((edge) => {
    edges.update({ id: edge.id, label: edge.subtype });
  });
}

function getWorkflowState(first) {
  stateUpdate = true;
  if (first) resetDisplay();
  const runtime = $("#current-runtimes").val();
  const url = runtime ? `/${runtime}` : "";
  if (workflow && workflow.id) {
    call(`/get_workflow_state/${workflow.id}${url}`, function(result) {
      if (result.workflow.last_modified !== lastModified) {
        displayWorkflow(result);
      }
      displayWorkflowState(result);
      if (first || (result.state && result.state.status == "Running")) {
        setTimeout(getWorkflowState, 3000);
      } else {
        stateUpdate = false;
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
      switchToWorkflow(workflow.id);
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
    $("#current-workflow,#current-runtimes").selectpicker({
      liveSearch: true,
    });
  });
})();
