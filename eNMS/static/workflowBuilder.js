/*
global
action: false
alertify: false
call: false
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
let hoveredNode;

function displayWorkflow(workflowData) {
  const wf = workflowData.workflow;
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
  graph.on("hoverNode", function(properties) {
    properties.event.preventDefault();
    let node = this.getNodeAt(properties.pointer.DOM);
    if (node) {
      node = parseInt(node);
      hoveredNode = node;
      const job = workflow.jobs.find((w) => w.id === node);
      nodes.update({ id: node, label: `${job.name}\n${job.type}` });
    }
  });
  graph.on("blurNode", function(properties) {
    const job = workflow.jobs.find((w) => w.id === hoveredNode);
    if (job) nodes.update({ id: hoveredNode, label: job.name });
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
  $(`#add_jobs option[value='${wf.id}']`).remove();
  $("#add_jobs").selectpicker("refresh");
  lastModified = wf.last_modified;
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
          nodes.add(jobToNode(job, index + 1));
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
    hoveredNode = null;

    lastModified = result.update_time;
    alertify.notify(
      `'${result.job.name}' deleted from the workflow.`,
      "success",
      5
    );
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
      ? index * 50 - 50
      : 0,
    y: job.positions[workflow.name]
      ? job.positions[workflow.name][1]
      : index
      ? index * 50 - 200
      : 0,
  };
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
  Run: (job) => showTypePanel(job.type, job.id, "run"),
  "Run Workflow": runWorkflow,
  "Run Workflow with Updates": () => runWorkflow(true),
  Results: (job) => showResultsPanel(job.id, job.label, "service"),
  "Create Workflow": () => showTypePanel("workflow"),
  "Edit Workflow": () => showTypePanel("workflow", workflow.id),
  "Workflow Results": () =>
    showResultsPanel(workflow.id, workflow.name, "workflow"),
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

function runWorkflow(withUpdates) {
  workflow.jobs.forEach((job) => colorJob(job.id, job.color));
  if (withUpdates) {
    showTypePanel("Workflow", workflow.id, "run");
  } else {
    normalRun(workflow.id);
  }
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
    result.workflow.jobs.forEach((job) => {
      colorJob(job.id, job.color);
    });
  } else {
    $("#status").text(`Status: ${result.state.status}`);
    if (result.state.current_job) {
      colorJob(result.state.current_job.id, "#89CFF0");
      $("#current-job").text(`Current job: ${result.state.current_job.name}.`);
    } else {
      $("#current-job").empty();
    }
    if (result.state.jobs) {
      $.each(result.state.jobs, (id, success) => {
        const color = {
          true: "#32cd32",
          false: "#FF6666",
          skipped: "#D3D3D3",
        };
        colorJob(id, color[success]);
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
      if (first || (result.state && result.state.is_running)) {
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
