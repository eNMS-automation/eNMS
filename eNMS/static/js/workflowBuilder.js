/*
global
action: false
linkRuntime: false
page: false
subtypes: false
serverUrl: false
theme: false
user: false
*/

import { field, runService, runLogic, showRuntimePanel } from "./automation.js";
import {
  call,
  configureNamespace,
  copyToClipboard,
  editors,
  moveHistory,
  notify,
  openPanel,
  showInstancePanel,
  showConfirmationPanel,
  userIsActive,
} from "./base.js";
import {
  configureGraph,
  currentMode,
  currentPath,
  edges,
  instance,
  nodes,
  setPath,
  showLabelPanel,
  switchMode,
  updateBuilderBindings,
} from "./builder.js";
import { tables } from "./table.js";

const options = {
  interaction: {
    hover: true,
    hoverConnectedEdges: false,
    multiselect: true,
  },
  manipulation: {
    enabled: false,
    addNode: function(data, callback) {},
    addEdge: function(data, callback) {
      if (data.from.length == 36 || data.to.length == 36) {
        notify("You cannot use a label to draw an edge.", "error", 5);
      } else if (data.to == startId) {
        notify("You cannot draw an edge to 'Start'.", "error", 5);
      } else if (data.from == endId) {
        notify("You cannot draw an edge from 'End'.", "error", 5);
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
  ...theme.workflow,
};

export let ends = new Set();
export let workflow = JSON.parse(localStorage.getItem("workflow"));
export let currentRuntime = linkRuntime;
export let graph;

let currentRun;
let currentPlaceholder;
let placeholder;
let isSuperworkflow;
let runtimeDisplay;
let runtimeDisplayFlip;
let startId;
let endId;

export function displayWorkflow(workflowData) {
  workflow = workflowData.service;
  placeholder = null;
  currentPlaceholder = workflowData.state?.[currentPath]?.placeholder;
  isSuperworkflow = false;
  graph = configureGraph(
    workflow,
    {
      nodes: workflow.services.map(drawWorkflowNode),
      edges: workflow.edges.map(drawWorkflowEdge),
    },
    options
  );
  workflow.services.map(drawIterationEdge);
  graph.on("click", function(event) {
    const node = this.getNodeAt(event.pointer.DOM);
    if (currentMode != "motion" && !node) switchMode("motion", true);
  });
  graph.on("doubleClick", function(event) {
    event.event.preventDefault();
    let node = nodes.get(this.getNodeAt(event.pointer.DOM));
    if (["Placeholder", "Start", "End"].includes(node.name)) node = currentPlaceholder;
    if (!node || !node.id) {
      return;
    } else if (node.type == "label") {
      showLabelPanel({ label: node, usePosition: true });
    } else if (node.type == "workflow") {
      switchToWorkflow(`${currentPath}>${node.id}`, null, $("#current-runtime").val());
    } else {
      showInstancePanel(node.type, node.id);
    }
  });
  const exportLocation = `location.href='/export_service/${workflow.id}'`;
  $("#export-workflow-btn").attr("onclick", exportLocation);
  displayWorkflowState(workflowData);
}

function updateRuntimes(result) {
  currentPlaceholder = result.state?.[currentPath]?.placeholder;
  if (!currentRuntime) currentRuntime = $("#current-runtime").val();
  const displayedRuntimes = result.runtimes.map((runtime) => runtime[0]);
  if (
    runtimeDisplayFlip &&
    !["normal", "latest"].includes(currentRuntime) &&
    !displayedRuntimes.includes(currentRuntime)
  ) {
    currentRuntime = "latest";
    runtimeDisplayFlip = false;
  }
  $("#current-runtime").empty();
  $("#current-runtime").append("<option value='normal'>Normal Display</option>");
  $("#current-runtime").append("<option value='latest'>Latest Runtime</option>");
  result.runtimes.forEach((runtime) => {
    const option = `<option value='${runtime[0]}'>${runtime[1]}</option>`;
    $("#current-runtime").append(option);
  });
  if (placeholder && currentPlaceholder) {
    nodes.update({
      id: placeholder.id,
      label: getServiceLabel(placeholder),
    });
  }
  $("#current-runtime").val(currentRuntime || "latest");
  $("#current-runtime").selectpicker("refresh");
}

export function flipRuntimeDisplay(display) {
  runtimeDisplay = display || (runtimeDisplay == "users" ? "user" : "users");
  runtimeDisplayFlip = true;
  localStorage.setItem("runtimeDisplay", runtimeDisplay);
  $("#runtime-display-icon").attr("class", `fa fa-${runtimeDisplay}`);
  if (!display) switchToWorkflow(currentPath);
}

export function showServicePanel(type, id, mode, tableId) {
  const postfix = tableId ? `-${tableId}` : "";
  const prefix = mode == "bulk-filter" ? `${type}_filtering` : type;
  const typeInput = $(id ? `#${type}-type-${id}` : `#${type}-type`);
  typeInput.val(type).prop("disabled", true);
  $(id ? `#${type}-name-${id}` : `#${type}-name`).prop("disabled", true);
  if (id && mode == "duplicate" && type == "workflow") $(`#copy-${id}`).val(id);
  const workflowId = id ? `#${type}-workflows-${id}` : `#${type}-workflows${postfix}`;
  if (id && mode == "duplicate") {
    const value = page == "workflow_builder" ? [workflow.name] : [];
    $(workflowId)
      .val(value)
      .trigger("change");
  }
  if (!id && workflow && page == "workflow_builder") {
    $(`#${type}-vendor`)
      .val(workflow.vendor)
      .trigger("change");
    $(`#${type}-operating_system`)
      .val(workflow.operating_system)
      .trigger("change");
  }
  $(field("report_template", type, id)).on("change", function() {
    const isJinja2 = this.value.endsWith(".j2");
    field("report_jinja2_template", type, id).prop("checked", isJinja2);
    call({
      url: `/get_report_template/${this.value}`,
      callback: function(template) {
        field("report", type, id).val(template);
      },
    });
  });
  $(workflowId).prop("disabled", true);
  const wizardId = id ? `#${prefix}-wizard-${id}` : `#${prefix}-wizard${postfix}`;
  $(wizardId).smartWizard({
    enableAllSteps: true,
    keyNavigation: false,
    transitionEffect: "none",
    onShowStep: function() {
      if (!editors[id]) return;
      Object.keys(editors[id]).forEach(function(field) {
        editors[id][field].refresh();
      });
    },
  });
  $(".buttonFinish,.buttonNext,.buttonPrevious").hide();
  $(wizardId).smartWizard("fixHeight");
}

export const switchToWorkflow = function(path, direction, runtime, selection) {
  if (typeof path === "undefined") return;
  if (path.toString().includes(">")) {
    $("#up-arrow").removeClass("disabled");
  } else {
    $("#up-arrow").addClass("disabled");
  }
  setPath(path);
  moveHistory(path, direction);
  call({
    url: `/get_service_state/${path}`,
    data: { display: runtimeDisplay, runtime: runtime || "latest" },
    callback: function(result) {
      workflow = result.service;
      currentRun = result.run;
      if (workflow?.superworkflow) {
        if (!currentPath.includes(workflow.superworkflow.id)) {
          setPath(`${workflow.superworkflow.id}>${path}`);
        }
        $("#up-arrow").removeClass("disabled");
      }
      localStorage.setItem("workflow_path", path);
      if (workflow) {
        localStorage.setItem("workflow", JSON.stringify(workflow));
      }
      displayWorkflow(result);
      if (selection) graph.setSelection(selection);
      switchMode(currentMode, true);
    },
  });
};

function updateWorkflowService(service) {
  nodes.add(drawWorkflowNode(service));
  workflow.services.push(service);
  switchMode("motion", true);
  notify(`Service '${service.scoped_name}' added to the workflow.`, "success", 5);
}

function addServicesToWorkflow() {
  const selection = $("#service-tree").jstree("get_checked", true);
  if (!selection.length) notify("Nothing selected.", "error", 5);
  $("#services").val(selection.map((n) => n.data.id));
  call({
    url: `/copy_service_in_workflow/${workflow.id}`,
    form: "add-services-form",
    callback: function(result) {
      instance.last_modified = result.update_time;
      $("#add_services_to_workflow").remove();
      result.services.map(updateWorkflowService);
    },
  });
}

function saveEdge(edge) {
  const param = `${workflow.id}/${edge.subtype}/${edge.from}/${edge.to}`;
  call({
    url: `/add_edge/${param}`,
    callback: function(result) {
      instance.last_modified = result.update_time;
      const newEdge = drawWorkflowEdge(result);
      edges.add(newEdge);
      workflow.edges.push(newEdge);
      graph.addEdgeMode();
    },
  });
}

function stopWorkflow() {
  if (!currentRun) notify("The workflow is not currently running.", "error", 5);
  const stop = function() {
    call({
      url: `/stop_run/${currentRun.runtime}`,
      callback: (result) => {
        if (!result) {
          notify("The workflow is not currently running.", "error", 5);
        } else {
          const log = `Workflow ${workflow.name} will stop after current service.`;
          notify(log, "success", 5, true);
        }
      },
    });
  };
  if (currentRun?.status === "Running" && user.name !== currentRun?.creator) {
    showConfirmationPanel({
      id: currentRun.id,
      title: "Workflow Stop Confirmation",
      message: `The workflow run you are attempting to stop was started
      by '${currentRun.creator}'.<br>Are you sure you want to stop it ?`,
      onConfirm: stop,
    });
  } else {
    stop();
  }
}

function skipServices() {
  const selectedNodes = graph.getSelectedNodes().filter((x) => !isNaN(x));
  if (!selectedNodes.length) return;
  call({
    url: `/skip_services/${workflow.id}/${selectedNodes.join("-")}`,
    callback: (result) => {
      instance.last_modified = result.update_time;
      workflow.services.forEach((service) => {
        if (selectedNodes.includes(service.id)) {
          service.skip[workflow.name] = result.skip === "skip";
          nodes.update({
            id: service.id,
            color: result.skip === "skip" ? "#D3D3D3" : "#D2E5FF",
          });
        }
      });
      notify(`Services ${result.skip}ped.`, "success", 5);
    },
  });
}

function getServiceLabel(service) {
  if (["Start", "End"].includes(service.scoped_name)) {
    return service.scoped_name;
  }
  let label =
    service.type == "workflow"
      ? `\n     ${service.scoped_name}     \n`
      : `${service.scoped_name}\n`;
  label += "—————\n";
  if (service.scoped_name == "Placeholder" && currentPlaceholder) {
    label += currentPlaceholder.scoped_name;
  } else {
    label +=
      service.type == "workflow" ? "Subworkflow" : subtypes["service"][service.type];
  }
  return label;
}

export function drawWorkflowNode(service) {
  const isPlaceholder = service.scoped_name == "Placeholder";
  if (isPlaceholder) {
    isSuperworkflow = true;
    placeholder = service;
  }
  const defaultService = ["Start", "End"].includes(service.scoped_name);
  if (defaultService) {
    ends.add(service.id);
    if (service.scoped_name == "Start") {
      startId = service.id;
    } else {
      endId = service.id;
    }
  }
  return {
    id: service.id,
    shape: service.type == "workflow" ? "ellipse" : defaultService ? "circle" : "box",
    color: defaultService ? "pink" : isPlaceholder ? "#E6ADD8" : "#D2E5FF",
    font: {
      size: 15,
      multi: "html",
      align: "center",
      bold: { color: "#000000" },
    },
    shadow: {
      enabled: !defaultService && !isPlaceholder,
      color: service.shared ? "#FF1694" : "#6666FF",
      size: 15,
    },
    label: getServiceLabel(service),
    name: service.scoped_name,
    type: service.type,
    x: service.x,
    y: service.y,
  };
}

export function drawIterationEdge(service) {
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
    title += `<b>Iteration Variable Name</b>: ${service.iteration_variable_name}`;
    const hoverDiv = document.createElement("div");
    hoverDiv.innerHTML = title;
    {
      edges.add({
        id: -service.id,
        label: "Iteration",
        from: service.id,
        to: service.id,
        color: "black",
        arrows: { to: { enabled: true } },
        title: hoverDiv,
        font: { vadjust: -15 },
      });
    }
  }
}

export function drawWorkflowEdge(edge) {
  return {
    id: edge.id,
    label: edge.label,
    type: edge.subtype,
    from: edge.source_id,
    to: edge.destination_id,
    smooth: {
      type: "curvedCW",
      roundness: edge.subtype == "success" ? 0.1 : edge.subtype == "failure" ? -0.1 : 0,
    },
    color: {
      color: edge.color,
    },
    arrows: { to: { enabled: true } },
  };
}

function addServicePanel() {
  openPanel({
    name: "add_services_to_workflow",
    title: "Add Services to Workflow",
    callback: function() {
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
        plugins: ["checkbox", "search", "types", "wholerow"],
        checkbox: {
          three_state: false,
        },
        search: {
          show_only_matches: true,
          ajax: {
            type: "POST",
            url: "/search_workflow_services",
          },
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
      let timer = false;
      $("#add-services-search").keyup(function(event) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(function() {
          $("#service-tree")
            .jstree(true)
            .search($("#add-services-search").val());
        }, 500);
      });
    },
  });
}

function getResultLink(service, device) {
  const link = `get_result("${service.name}"${device ? ", device=device.name" : ""})`;
  copyToClipboard({ text: link });
}

function getWorkflowLink(includeRuntime) {
  const baseUrl =
    serverUrl || `${window.location.protocol}//${window.location.hostname}`;
  let link = `${baseUrl}/workflow_builder/${currentPath}`;
  if (includeRuntime) link += `/${currentRuntime}`;
  copyToClipboard({ text: encodeURI(link) });
}

export function updateWorkflowRightClickBindings() {
  updateBuilderBindings(action);
  Object.assign(action, {
    "Link to Workflow": () => getWorkflowLink(),
    "Link to Runtime": () => getWorkflowLink(true),
    "Run Workflow": () => runWorkflow(),
    "Parameterized Workflow Run": () => runWorkflow(true),
    "Restart Workflow from Here": showRestartWorkflowPanel,
    "Workflow Result Tree": () => showRuntimePanel("results", workflow),
    "Workflow Result Table": () =>
      showRuntimePanel("results", workflow, null, "full_result", null, true),
    "Workflow Report": () => showRuntimePanel("report", workflow),
    "Workflow Result Comparison": () => compareWorkflowResults(),
    "Workflow Logs": () => showRuntimePanel("logs", workflow),
    "Add to Workflow": addServicePanel,
    "Stop Workflow": () => stopWorkflow(),
    "Runtimes Display": flipRuntimeDisplay,
    "Service Name": (service) => copyToClipboard({ text: service.name }),
    "Top-level Result": getResultLink,
    "Per-device Result": (node) => getResultLink(node, true),
    "Create 'Success' edge": () => switchMode("success"),
    "Create 'Failure' edge": () => switchMode("failure"),
    "Move Nodes": () => switchMode("motion"),
    "Edit Edge": (edge) => {
      showInstancePanel("workflow_edge", edge.id);
    },
    Skip: () => skipServices(),
  });
}

function runWorkflow(parametrization) {
  if (isSuperworkflow) {
    return notify("A superworkflow cannot be run directly.", "error", 5);
  }
  resetWorkflowDisplay();
  runService({
    id: workflow.id,
    path: currentPath,
    parametrization: parametrization || workflow.mandatory_parametrization,
  });
}

function showRestartWorkflowPanel() {
  openPanel({
    name: "restart_workflow",
    title: `Restart Workflow '${workflow.name}'`,
    id: workflow.id,
    callback: function() {
      $(`#restart_workflow-start_services-${workflow.id}`).val(
        graph
          .getSelectedNodes()
          .filter((node) => !ends.has(node))
          .join("-")
      );
      call({
        url: `/get_runtimes/${workflow.id}`,
        data: { display: runtimeDisplay },
        callback: function(runtimes) {
          const id = `#restart_workflow-restart_runtime-${workflow.id}`;
          let currentIndex = 0;
          runtimes.forEach((runtime, index) => {
            if (runtime[0] == currentRuntime) currentIndex = index;
            $(id).append(new Option(runtime[1], runtime[0]));
          });
          $(id)
            .val(runtimes[currentIndex])
            .selectpicker("refresh");
        },
      });
    },
  });
}

function restartWorkflow() {
  call({
    url: `/run_service/${currentPath}`,
    form: `restart_workflow-form-${workflow.id}`,
    callback: function(result) {
      $(`#restart_workflow-${workflow.id}`).remove();
      runLogic(result);
    },
  });
}

export function colorService(id, color) {
  if (!ends.has(id) && nodes && nodes.get(id)) {
    nodes.update({ id: id, color: color });
  }
}

export function getServiceState(id, first) {
  call({
    url: `/get_service_state/${id}`,
    data: { display: runtimeDisplay },
    callback: function(result) {
      if (first || result.state?.status == "Running") {
        colorService(id, "#89CFF0");
        if (result.service && result.service.type === "workflow") {
          localStorage.setItem("workflow_path", id);
          localStorage.setItem("workflow", JSON.stringify(result.service));
        }
        setTimeout(() => getServiceState(id), 300);
      } else {
        colorService(id, "#D2E5FF");
      }
    },
  });
}

function displayWorkflowState(result) {
  if ($("#workflow-search").val()) return;
  resetWorkflowDisplay();
  updateRuntimes(result);
  if (currentRuntime == "normal") return;
  if (!nodes || !edges || !result.state) return;
  if (result.device_state) {
    for (const [serviceId, status] of Object.entries(result.device_state)) {
      colorService(parseInt(serviceId), status ? "#32cd32" : "#FF6666");
    }
    return;
  }
  let nodeUpdates = [];
  let edgeUpdates = [];
  const serviceIds = workflow.services.map((s) => s.id);
  for (let [path, state] of Object.entries(result.state)) {
    const id = parseInt(path.split(">").slice(-1)[0]);
    if (ends.has(id) || !serviceIds.includes(id)) continue;
    let label = `<b>${nodes.get(id).name}</b>\n`;
    colorService(id, state.success ? "#32cd32" : "#FF6666");
    let first = true;
    for (const progressKey of ["device", "iteration_device"]) {
      if (state.progress?.[progressKey]) {
        const total = parseInt(state.progress?.[progressKey]?.total) || 0;
        const success = parseInt(state.progress?.[progressKey]?.success) || 0;
        const skipped = parseInt(state.progress?.[progressKey]?.skipped) || 0;
        const failure = parseInt(state.progress?.[progressKey]?.failure) || 0;
        colorService(
          id,
          state.status == "Skipped" || (total && skipped == total)
            ? "#D3D3D3"
            : success + failure + skipped < total
            ? "#89CFF0"
            : state.success === false || failure > 0
            ? "#FF6666"
            : state.success === true
            ? "#32cd32"
            : "#00CCFF"
        );
        if (total) {
          const prefix = progressKey == "device" ? "Devices" : "Iteration";
          let progressLabel = `${prefix} - ${success + failure + skipped}/${total}`;
          const separator = first ? "—————\n" : "";
          label += `${separator}${progressLabel}`;
          let progressInfo = [];
          if (success) progressInfo.push(`${success} passed`);
          if (failure) progressInfo.push(`${failure} failed`);
          if (skipped) progressInfo.push(`${skipped} skipped`);
          const detailedLabel = ` (${progressInfo.join(", ")})${first ? "\n" : ""}`;
          if (progressInfo.length) label += detailedLabel;
          first = false;
        }
      }
    }
    nodeUpdates.push({
      id: id,
      label: label,
    });
  }
  nodes.update(nodeUpdates);
  const state = result.state[currentPath];
  if (state?.edges) {
    for (let [id, devices] of Object.entries(state.edges)) {
      if (!edges.get(parseInt(id))) continue;
      edgeUpdates.push({
        id: parseInt(id),
        label: isNaN(devices)
          ? `<b>${devices}</b>`
          : `<b>${devices} DEVICE${devices == 1 ? "" : "S"}</b>`,
        font: { size: 15, multi: "html" },
      });
    }
    edges.update(edgeUpdates);
  }
}

export function resetWorkflowDisplay() {
  let nodeUpdates = [];
  let edgeUpdates = [];
  workflow.services.forEach((service) => {
    if (service.scoped_name == "Placeholder") {
      nodeUpdates.push({
        id: service.id,
        label: "Placeholder",
      });
    } else if (ends.has(service.id) || !nodes) {
      return;
    } else {
      nodeUpdates.push({
        id: service.id,
        label: getServiceLabel(service),
        color: service.skip[workflow.name] ? "#D3D3D3" : "#D2E5FF",
      });
    }
  });
  if (nodes) nodes.update(nodeUpdates);
  if (edges) {
    workflow.edges.forEach((edge) => {
      edgeUpdates.push({ id: edge.id, label: edge.label });
    });
    edges.update(edgeUpdates);
  }
}

export function getWorkflowState(periodic, first) {
  const runtime = $("#current-runtime").val();
  if (userIsActive && workflow?.id && !first) {
    call({
      url: `/get_service_state/${currentPath}`,
      data: {
        display: runtimeDisplay,
        runtime: runtime,
        device: $("#device-filter").val(),
      },
      callback: function(result) {
        if (!Object.keys(result).length || result.service.id != workflow.id) return;
        currentRun = result.run;
        currentRuntime = result.runtime;
        if (result.service.last_modified > instance.last_modified) {
          displayWorkflow(result);
        } else {
          displayWorkflowState(result);
        }
      },
    });
  }
  if (periodic) setTimeout(() => getWorkflowState(true, false), 4000);
}

function compareWorkflowResults() {
  const mainId = parseInt(currentPath.split(">")[0]);
  openPanel({
    content: `
      <div class="modal-body">
        <div id="tooltip-overlay" class="overlay"></div>
        <form
          id="search-form-full_result-${mainId}"
          class="form-horizontal form-label-left"
          method="post"
        >
          <nav
            id="controls-full_result-${mainId}"
            class="navbar navbar-default nav-controls"
            role="navigation"
          >
            <button
              style="background:transparent; border:none; color:transparent;"
              type="button"
            ></button>
          </nav>
          <table
            id="table-full_result-${mainId}"
            class="table table-striped table-bordered table-hover"
            cellspacing="0"
            width="100%"
          ></table>
        </form>
      </div>`,
    size: "1000 600",
    name: "result_comparison",
    type: "full_result",
    title: "Result Comparison",
    id: mainId,
    tableId: `full_result-${mainId}`,
    callback: function() {
      let constraints = {
        parent_service_id: currentPath.split(">")[0],
        parent_service_id_filter: "equality",
      };
      // eslint-disable-next-line new-cap
      new tables["full_result"](mainId, constraints);
    },
  });
}

function filterDevice() {
  $("#device-filter-div").toggle();
  if (!$("#device-filter-div").is(":visible")) {
    $("#device-filter")
      .val(null)
      .trigger("change");
    getWorkflowState();
  }
}

configureNamespace("workflowBuilder", [
  addServicesToWorkflow,
  filterDevice,
  getWorkflowState,
  restartWorkflow,
  stopWorkflow,
  switchToWorkflow,
]);
