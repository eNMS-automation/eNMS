/*
global
action: false
alertify: false
arrowHistory: false
arrowPointer: false
call: false
createPanel: false
currentPath: true
currentRuntime: true
fCall: false
normalRun: false
runLogic: false
serviceTypes: false
Set: false
showPanel: false
showRuntimePanel: false
showTypePanel: false
switchToWorkflow: false
userIsActive: true
vis: false
workflow: true
*/

vis.Network.prototype.zoom = function(scale) {
  const animationOptions = {
    scale: this.getScale() + scale,
    animation: { duration: 300 },
  };
  this.view.moveTo(animationOptions);
};

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
    multiselect: true,
  },
  manipulation: {
    enabled: false,
    addNode: function(data, callback) {},
    addEdge: function(data, callback) {
      if (data.to == "Start") {
        alertify.notify("You cannot draw an edge to 'Start'.", "error", 5);
      } else if (data.from == "End") {
        alertify.notify("You cannot draw an edge from 'End'.", "error", 5);
      } else if (data.from != data.to) {
        data.subtype = currentMode;
        saveEdge(data);
      }
    },
    deleteNode: function(data, callback) {
      data.nodes = data.nodes.filter((node) => !ends.has(node));
      callback(data);
    },
  },
};

let nodes;
let edges;
let graph;
let selectedObject;
let ends = new Set();
let currentMode = "motion";
let creationMode;
let mousePosition;
let currLabel;
let triggerMenu;

function displayWorkflow(workflowData) {
  workflow = workflowData.service;
  nodes = new vis.DataSet(workflow.services.map(serviceToNode));
  edges = new vis.DataSet(workflow.edges.map(edgeToEdge));
  workflow.services.map(drawIterationEdge);
  for (const [id, label] of Object.entries(workflow.labels)) {
    drawLabel(id, label);
  }
  graph = new vis.Network(container, { nodes: nodes, edges: edges }, dsoptions);
  graph.setOptions({ physics: false });
  graph.on("oncontext", function(properties) {
    if (triggerMenu) {
      // eslint-disable-next-line new-cap
      mousePosition = graph.DOMtoCanvas({
        x: properties.event.offsetX,
        y: properties.event.offsetY,
      });
      properties.event.preventDefault();
      const node = this.getNodeAt(properties.pointer.DOM);
      const edge = this.getEdgeAt(properties.pointer.DOM);
      if (typeof node !== "undefined" && !ends.has(node)) {
        graph.selectNodes([node]);
        $(".menu-entry ").hide();
        $(`.${node.length == 36 ? "label" : "node"}-selection`).show();
        selectedObject = nodes.get(node);
        $(".workflow-selection").toggle(selectedObject.type == "workflow");
      } else if (typeof edge !== "undefined" && !ends.has(node)) {
        graph.selectEdges([edge]);
        $(".menu-entry ").hide();
        $(".edge-selection").show();
        selectedObject = edges.get(edge);
      } else {
        $(".menu-entry ").hide();
        $(".global").show();
      }
    } else {
      properties.event.stopPropagation();
      properties.event.preventDefault();
    }
  });
  graph.on("doubleClick", function(event) {
    event.event.preventDefault();
    const node = nodes.get(this.getNodeAt(event.pointer.DOM));
    if (!node.id) {
      return;
    } else if (node.type == "label") {
      editLabel(node);
    } else if (node.type == "workflow") {
      switchToWorkflow(`${currentPath}>${node.id}`);
    } else {
      showTypePanel(node.type, node.id);
    }
  });
  $("#current-runtime").empty();
  $("#current-runtime").append(
    "<option value='normal'>Normal Display</option>"
  );
  $("#current-runtime").append(
    "<option value='latest'>Latest Runtime</option>"
  );
  workflowData.runtimes.forEach((runtime) => {
    $("#current-runtime").append(
      `<option value='${runtime[0]}'>${runtime[0]} (run by ${
        runtime[1]
      })</option>`
    );
  });
  $("#current-runtime").val("latest");
  $("#current-workflow").val(currentPath.split(">")[0]);
  $("#current-runtime,#current-workflow").selectpicker("refresh");
  graph.on("dragEnd", (event) => {
    if (graph.getNodeAt(event.pointer.DOM)) savePositions();
  });
  displayWorkflowState(workflowData);
  rectangleSelection($("#network"), graph, nodes);
  switchMode(currentMode, true);
}

const rectangleSelection = (container, network, nodes) => {
  const offsetLeft = container.position().left - container.offset().left;
  const offsetTop = container.position().top - container.offset().top;
  let drag = false;
  let DOMRect = {};

  const canvasify = (DOMx, DOMy) => {
    // eslint-disable-next-line new-cap
    const { x, y } = network.DOMtoCanvas({ x: DOMx, y: DOMy });
    return [x, y];
  };

  const correctRange = (start, end) =>
    start < end ? [start, end] : [end, start];

  const selectFromDOMRect = () => {
    const [sX, sY] = canvasify(DOMRect.startX, DOMRect.startY);
    const [eX, eY] = canvasify(DOMRect.endX, DOMRect.endY);
    const [startX, endX] = correctRange(sX, eX);
    const [startY, endY] = correctRange(sY, eY);
    triggerMenu = startX == endX && startY == endY;
    if (triggerMenu) return;
    network.selectNodes(
      nodes.get().reduce((selected, { id }) => {
        const { x, y } = network.getPositions(id)[id];
        return startX <= x && x <= endX && startY <= y && y <= endY
          ? selected.concat(id)
          : selected;
      }, [])
    );
  };

  container.on("mousedown", function({ which, pageX, pageY }) {
    if (which === 3) {
      Object.assign(DOMRect, {
        startX: pageX - this.offsetLeft + offsetLeft,
        startY: pageY - this.offsetTop + offsetTop,
        endX: pageX - this.offsetLeft + offsetLeft,
        endY: pageY - this.offsetTop + offsetTop,
      });
      drag = true;
    }
  });

  container.on("mousemove", function({ which, pageX, pageY }) {
    if (which === 0 && drag) {
      drag = false;
      network.redraw();
    } else if (drag) {
      Object.assign(DOMRect, {
        endX: pageX - this.offsetLeft + offsetLeft,
        endY: pageY - this.offsetTop + offsetTop,
      });
      network.redraw();
    }
  });

  container.on("mouseup", function({ which }) {
    if (which === 3) {
      drag = false;
      network.redraw();
      selectFromDOMRect();
    }
  });

  network.on("afterDrawing", (ctx) => {
    if (drag) {
      const [startX, startY] = canvasify(DOMRect.startX, DOMRect.startY);
      const [endX, endY] = canvasify(DOMRect.endX, DOMRect.endY);
      ctx.setLineDash([5]);
      ctx.strokeStyle = "rgba(78, 146, 237, 0.75)";
      ctx.strokeRect(startX, startY, endX - startX, endY - startY);
      ctx.setLineDash([]);
      ctx.fillStyle = "rgba(151, 194, 252, 0.45)";
      ctx.fillRect(startX, startY, endX - startX, endY - startY);
    }
  });
};

// eslint-disable-next-line
function switchToSubworkflow() {
  const service = nodes.get(graph.getSelectedNodes()[0]);
  if (service.type != "workflow") {
    alertify.notify("You must select a subworkflow.", "error", 5);
  } else {
    switchToWorkflow(service.id);
  }
}

// eslint-disable-next-line
function processWorkflowData(instance, id) {
  if (!instance.type) {
    edges.update(edgeToEdge(instance));
  } else if (instance.type.includes("service") || instance.type == "workflow") {
    if (id) {
      if (workflow.id == id) return;
      nodes.update(serviceToNode(instance));
      let serviceIndex = workflow.services.findIndex(
        (s) => s.id == instance.id
      );
      workflow.services[serviceIndex] = instance;
    } else {
      if (creationMode == "create_workflow") {
        if (instance.type === "workflow" && !id) {
          $("#current-workflow").append(
            `<option value="${instance.id}">${instance.name}</option>`
          );
          $("#current-workflow")
            .val(instance.id)
            .trigger("change");
          displayWorkflow({ service: instance, runtimes: [] });
        }
      } else {
        call(
          `/add_service_to_workflow/${workflow.id}/${instance.id}`,
          function() {
            updateWorkflowService(instance);
          }
        );
      }
    }
    drawIterationEdge(instance);
  }
}

// eslint-disable-next-line
function updateWorkflowService(service) {
  nodes.add(serviceToNode(service));
  workflow.services.push(service);
  alertify.notify(
    `Service '${service.scoped_name}' added to the workflow.`,
    "success",
    5
  );
}

// eslint-disable-next-line
function addServicesToWorkflow() {
  const selection = $("#service-tree").jstree("get_checked", true);
  if (!selection.length) alertify.notify("Nothing selected.", "error", 5);
  $("#services").val(selection.map((n) => n.data.id));
  fCall(
    `/copy_service_in_workflow/${workflow.id}`,
    "#add-services-form",
    function(result) {
      workflow.last_modified = result.update_time;
      $("#add_services").remove();
      result.services.map(updateWorkflowService);
    }
  );
}

function deleteNode(id) {
  let node = nodes.get(id);
  if (node.type == "label") {
    deleteLabel(node);
  } else {
    workflow.services = workflow.services.filter((n) => n.id != id);
    call(`/delete_node/${workflow.id}/${id}`, function(result) {
      workflow.last_modified = result.update_time;
      alertify.notify(
        `'${result.service.scoped_name}' deleted from the workflow.`,
        "success",
        5
      );
    });
  }
}

function deleteLabel(label, noNotification) {
  nodes.remove(label.id);
  call(`/delete_label/${workflow.id}/${label.id}`, function(updateTime) {
    delete workflow.labels[label.id];
    workflow.last_modified = updateTime;
    if (!noNotification) alertify.notify("Label removed.", "success", 5);
  });
}

function saveEdge(edge) {
  const param = `${workflow.id}/${edge.subtype}/${edge.from}/${edge.to}`;
  call(`/add_edge/${param}`, function(result) {
    workflow.last_modified = result.update_time;
    edges.add(edgeToEdge(result.edge));
    graph.addEdgeMode();
  });
}

function deleteEdge(edgeId) {
  workflow.edges = workflow.edges.filter((e) => e.id != edgeId);
  call(`/delete_edge/${workflow.id}/${edgeId}`, (updateTime) => {
    workflow.last_modified = updateTime;
  });
}

function stopWorkflow() {
  call(`/stop_workflow/${currentRuntime}`, (result) => {
    if (!result) {
      alertify.notify("The workflow is not currently running.", "error", 5);
    } else {
      alertify.notify(
        "Workflow will stop after current service...",
        "success",
        5
      );
    }
  });
}

// eslint-disable-next-line
function skipServices() {
  const selectedNodes = graph.getSelectedNodes().filter((x) => !isNaN(x));
  if (!selectedNodes.length) return;
  call(`/skip_services/${workflow.id}/${selectedNodes.join("-")}`, (skip) => {
    getWorkflowState();
    alertify.notify(`Services ${skip}ped.`, "success", 5);
  });
}

function formatServiceTitle(service) {
  let title = `
    <b>Type</b>: ${service.type}<br>
    <b>Name</b>: ${service.name}<br>
  `;
  if (service.description) {
    title += `<b>Description</b>: ${service.description}`;
  }
  return title;
}

function getServiceLabel(service) {
  if (ends.has(service.id)) {
    return service.scoped_name;
  }
  let label =
    service.type == "workflow"
      ? `\n     ${service.scoped_name}     \n`
      : `${service.scoped_name}\n`;
  label += "—————\n";
  label +=
    service.type == "workflow" ? "Subworkflow" : serviceTypes[service.type];
  return label;
}

function serviceToNode(service) {
  const defaultService = ["Start", "End"].includes(service.scoped_name);
  if (defaultService) ends.add(service.id);
  return {
    id: service.id,
    shape:
      service.type == "workflow"
        ? "ellipse"
        : defaultService
        ? "circle"
        : "box",
    color: defaultService ? "pink" : "#D2E5FF",
    font: {
      size: 15,
      multi: "html",
      align: "center",
      bold: { color: "#000000" },
    },
    shadow: {
      enabled: !defaultService,
      color: service.shared ? "#FF1694" : "#6666FF",
      size: 15,
    },
    label: getServiceLabel(service),
    name: service.scoped_name,
    type: service.type,
    title: formatServiceTitle(service),
    x: service.positions[workflow.name]
      ? service.positions[workflow.name][0]
      : 0,
    y: service.positions[workflow.name]
      ? service.positions[workflow.name][1]
      : 0,
  };
}

function drawLabel(id, label) {
  nodes.add({
    id: id,
    shape: "box",
    type: "label",
    font: { align: label.alignment || "center" },
    label: label.content,
    borderWidth: 0,
    color: "#FFFFFF",
    x: label.positions[0],
    y: label.positions[1],
  });
}

function drawIterationEdge(service) {
  if (!service.iteration_values && !service.iteration_devices) {
    edges.remove(-service.id);
  } else if (!edges.get(-service.id)) {
    let title = "";
    if (service.iteration_devices) {
      title += `<b>Iteration Devices</b>: ${service.iteration_devices}<br>`;
    }
    if (service.iteration_values) {
      title += `<b>Iteration Values</b>: ${service.iteration_values}<br>`;
    }
    title += `<b>Iteration Variable Name</b>: ${
      service.iteration_variable_name
    }`;
    {
      edges.add({
        id: -service.id,
        label: "Iteration",
        from: service.id,
        to: service.id,
        color: "black",
        arrows: { to: { enabled: true } },
        title: title,
      });
    }
  }
}

function edgeToEdge(edge) {
  return {
    id: edge.id,
    label: edge.label,
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
  graph
    .getSelectedNodes()
    .filter((node) => !ends.has(node))
    .map((node) => deleteNode(node));
  graph.getSelectedEdges().map((edge) => deleteEdge(edge));
  graph.deleteSelected();
  switchMode(currentMode, true);
}

function switchMode(mode, noNotification) {
  const oldMode = currentMode;
  currentMode =
    mode || (currentMode == "motion" ? $("#edge-type").val() : "motion");
  if (
    (oldMode == "motion" || currentMode == "motion") &&
    oldMode != currentMode
  ) {
    $("#mode-icon")
      .toggleClass("glyphicon-move")
      .toggleClass("glyphicon-random");
  }
  let notification;
  if (currentMode == "motion") {
    graph.addNodeMode();
    notification = "Mode: Motion.";
  } else {
    graph.addEdgeMode();
    notification = `Mode: Creation of '${currentMode}' Edge.`;
  }
  if (!noNotification) alertify.notify(notification, "success", 5);
}

$("#current-workflow").on("change", function() {
  if (!workflow || this.value != workflow.id) switchToWorkflow(this.value);
});

$("#current-runtime").on("change", function() {
  getWorkflowState();
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
        workflow.last_modified = updateTime;
      } else {
        alertify.notify("HTTP Error 403 – Forbidden", "error", 5);
      }
    },
  });
}

function addServicePanel() {
  showPanel("add_services", null, function() {
    $("#service-tree").jstree({
      core: {
        animation: 200,
        themes: { stripes: true },
        data: {
          url: function(node) {
            const nodeId = node.id == "#" ? "all" : node.data.id;
            return `/get_workflow_services/${workflow.id}/${nodeId}`;
          },
          type: "POST",
        },
      },
      plugins: ["checkbox", "types"],
      checkbox: {
        three_state: false,
      },
      types: {
        category: {
          icon: "fa fa-folder",
        },
        default: {
          icon: "glyphicon glyphicon-file",
        },
        workflow: {
          icon: "fa fa-sitemap",
        },
      },
    });
  });
}

function createNew(mode) {
  creationMode = mode;
  if (mode == "create_workflow") {
    showTypePanel("workflow");
  } else if (mode == "duplicate_workflow") {
    call(`/duplicate_workflow/${workflow.id}`, function(instance) {
      $("#current-workflow").append(
        `<option value="${instance.id}">${instance.name}</option>`
      );
      switchToWorkflow(instance.id);
    });
  } else {
    showTypePanel($("#service-type").val());
  }
}

Object.assign(action, {
  "Run Workflow": () => runWorkflow(),
  "Parameterized Workflow Run": () => runWorkflow(true),
  "Create Workflow": () => createNew("create_workflow"),
  "Duplicate Workflow": () => createNew("duplicate_workflow"),
  "Create New Service": () => createNew("create_service"),
  "Edit Workflow": () => showTypePanel("workflow", workflow.id),
  "Restart Workflow from Here": (service) =>
    showRestartWorkflowPanel(workflow, service),
  "Workflow Results": () => showRuntimePanel("results", workflow),
  "Workflow Logs": () => showRuntimePanel("logs", workflow),
  "Add to Workflow": addServicePanel,
  "Stop Workflow": () => stopWorkflow(),
  Delete: deleteSelection,
  "Create 'Success' edge": () => switchMode("success"),
  "Create 'Failure' edge": () => switchMode("failure"),
  "Create 'Prerequisite' edge": () => switchMode("prerequisite"),
  "Move Nodes": () => switchMode("motion"),
  "Create Label": () => showPanel("workflow_label"),
  "Edit Label": editLabel,
  "Edit Edge": (edge) => {
    showTypePanel("workflow_edge", edge.id);
  },
  "Delete Label": deleteLabel,
  Skip: () => skipServices(),
  "Zoom In": () => graph.zoom(0.2),
  "Zoom Out": () => graph.zoom(-0.2),
  "Enter Workflow": (node) => switchToWorkflow(`${currentPath}>${node.id}`),
  Backward: () => switchToWorkflow(arrowHistory[arrowPointer - 1], "left"),
  Forward: () => switchToWorkflow(arrowHistory[arrowPointer + 1], "right"),
  Upward: () => {
    const parentPath = currentPath
      .split(">")
      .slice(0, -1)
      .join(">");
    if (parentPath) switchToWorkflow(parentPath);
  },
});

// eslint-disable-next-line
function createLabel() {
  const pos = currLabel
    ? [currLabel.x, currLabel.y]
    : mousePosition
    ? [mousePosition.x, mousePosition.y]
    : [0, 0];
  const params = `${workflow.id}/${pos[0]}/${pos[1]}`;
  fCall(`/create_label/${params}`, "#workflow_label-form", function(result) {
    if (currLabel) {
      deleteLabel(currLabel, true);
      currLabel = null;
    }
    drawLabel(result.id, result);
    $("#workflow_label").remove();
    alertify.notify("Label created.", "success", 5);
  });
}

function editLabel(label) {
  showPanel("workflow_label", null, () => {
    $("#text").val(label.label);
    $("#alignment")
      .val(label.font.align)
      .selectpicker("refresh");
    currLabel = label;
  });
}

$("#network").contextMenu({
  menuSelector: "#contextMenu",
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selectedObject);
  },
});

function runWorkflow(withUpdates) {
  resetDisplay();
  if (withUpdates) {
    showTypePanel("workflow", workflow.id, "run");
  } else {
    normalRun(workflow.id);
  }
}

function showRestartWorkflowPanel(workflow, service) {
  createPanel(
    "restart_workflow",
    `Restart Workflow '${workflow.name}' from '${service.name}'`,
    workflow.id,
    function() {
      $("#start_services").append(new Option(service.name, service.id));
      $("#start_services")
        .val(service.id)
        .trigger("change");
      call(`/get_runtimes/service/${workflow.id}`, function(runtimes) {
        runtimes.forEach((runtime) => {
          $("#restart_runtime").append(
            $("<option></option>")
              .attr("value", runtime[0])
              .text(runtime[1])
          );
        });
        $("#restart_runtime").val(runtimes[runtimes.length - 1]);
        $("#restart_runtime").selectpicker("refresh");
      });
    }
  );
}

// eslint-disable-next-line
function restartWorkflow() {
  fCall(`/run_service/${currentPath}`, `#restart_workflow-form`, function(
    result
  ) {
    $(`#restart_workflow-${workflow.id}`).remove();
    runLogic(result);
  });
}

function colorService(id, color) {
  if (!ends.has(id) && nodes) {
    nodes.update({ id: id, color: color });
  }
}

// eslint-disable-next-line
function getServiceState(id, first) {
  call(`/get_service_state/${id}`, function(result) {
    if (first || result.state.status == "Running") {
      colorService(id, "#89CFF0");
      $("#status").text("Status: Running.");
      setTimeout(() => getServiceState(id), 300);
    } else {
      $("#status").text("Status: Idle.");
      colorService(id, "#D2E5FF");
    }
  });
}

// eslint-disable-next-line
function displayWorkflowState(result) {
  if (!nodes || !edges) return;
  resetDisplay();
  if (!result.state) {
    $("#progress").hide();
  } else if (result.state.progress) {
    const mode = result.state.progress.device.total ? "device" : "service";
    const progress = result.state.progress[mode];
    $("#progress").show();
    $("#progress-success").width(
      `${(progress.success * 100) / progress.total}%`
    );
    $("#progress-failure").width(
      `${(progress.failure * 100) / progress.total}%`
    );
    if (progress.success) $("#progress-success-span").text(progress.success);
    if (progress.failure) $("#progress-failure-span").text(progress.failure);
    $("#status").text(`Status: ${result.state.status}`);
    if (result.state.services) {
      $.each(result.state.services, (path, state) => {
        const id = parseInt(path.split(">").slice(-1)[0]);
        if (ends.has(id) || !(id in nodes._data)) return;
        const color = {
          true: "#32cd32",
          false: "#FF6666",
          skipped: "#D3D3D3",
          null: "#00CCFF",
        };
        colorService(id, color[state.success]);
        const progress = state.progress.device;
        if (progress.total) {
          let label = `<b>${nodes.get(id).name}</b>\n`;
          label += "—————\n";
          let progressLabel = `Progress - ${progress.success +
            progress.failure}/${progress.total}`;
          progressLabel += ` (${progress.success} passed, ${
            progress.failure
          } failed)`;
          label += progressLabel;
          nodes.update({
            id: id,
            label: label,
          });
        }
      });
    }
    if (result.state.edges) {
      $.each(result.state.edges, (id, devices) => {
        if (!edges.get(id)) return;
        edges.update({
          id: id,
          label:
            typeof devices == "string"
              ? `<b>${devices}</b>`
              : `<b>${devices} DEVICE${devices == 1 ? "" : "S"}</b>`,
          font: { size: 15, multi: "html" },
        });
      });
    }
  }
}

function resetDisplay() {
  $("#progressbar").hide();
  workflow.services.forEach((service) => {
    if (ends.has(service.id)) return;
    nodes.update({
      id: service.id,
      label: getServiceLabel(service),
      color: service.skip ? "#D3D3D3" : "#D2E5FF",
    });
  });
  if (!edges) return;
  workflow.edges.forEach((edge) => {
    edges.update({ id: edge.id, label: edge.label });
  });
}

function getWorkflowState(periodic, notification) {
  const runtime = $("#current-runtime").val();
  const url = runtime ? `/${runtime}` : "";
  if (userIsActive && workflow && workflow.id) {
    call(`/get_service_state/${currentPath}${url}`, function(result) {
      if (result.service.id != workflow.id) return;
      currentRuntime = result.runtime;
      if (result.service.last_modified !== workflow.last_modified) {
        displayWorkflow(result);
      } else {
        displayWorkflowState(result);
      }
    });
  }
  if (periodic) setTimeout(() => getWorkflowState(true), 4000);
  if (notification) alertify.notify("Workflow refreshed.", "success", 5);
}

(function() {
  $("#left-arrow,#right-arrow").addClass("disabled");
  $("#edge-type").on("change", function() {
    switchMode(this.value);
  });
  call("/get_top_level_workflows", function(workflows) {
    workflows.sort((a, b) => a.name.localeCompare(b.name));
    for (let i = 0; i < workflows.length; i++) {
      $("#current-workflow").append(
        `<option value="${workflows[i].id}">${workflows[i].name}</option>`
      );
    }
    if (workflow) {
      $("#current-workflow").val(currentPath.split(">")[0]);
      switchToWorkflow(currentPath);
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
    $("#edge-type").selectpicker();
    getWorkflowState(true);
  });
})();
