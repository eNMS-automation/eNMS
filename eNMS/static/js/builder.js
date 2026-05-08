/*
global
action: true
linkPath: false
page: false
subtypes: false
user: false
vis: false
*/

import { flipRuntimeDisplay, runtimeDisplay } from "./automation.js";
import {
  call,
  configureNamespace,
  createTooltips,
  history,
  historyPosition,
  initSelect,
  loadTypes,
  notify,
  openPanel,
  showChangelogPanel,
  showConfirmationPanel,
  showInstancePanel,
} from "./base.js";
import {
  drawNetworkEdge,
  drawNetworkNode,
  getNetworkState,
  switchToNetwork,
  updateNetworkRightClickBindings,
} from "./networkBuilder.js";
import {
  drawIterationEdge,
  drawWorkflowEdge,
  drawWorkflowNode,
  ends,
  getWorkflowState,
  switchToWorkflow,
  updateWorkflowRightClickBindings,
} from "./workflowBuilder.js";

const container = document.getElementById("builder");
const type = page.includes("network") ? "network" : "workflow";
const nodeType = type == "network" ? "device" : "service";
const savedPath = linkPath || localStorage.getItem(`${type}_path`);
let currentLabel;
let network;
let selectedObject;
let builderTreeData;
export let creationMode;
export let currentMode = "motion";
export let currentPath = page.includes("builder") && savedPath;
export let idToPid = {};
export let instance;
export let edges;
export let mousePosition;
export let nodes;
export let pidToId = {};
export let treeIsDisplayed = user.display_tree;
export let triggerMenu;

export function configureGraph(newInstance, graph, options) {
  nodes = new vis.DataSet(graph.nodes);
  edges = new vis.DataSet(graph.edges);
  instance = newInstance;
  for (const [id, label] of Object.entries(instance.labels)) {
    drawLabel(id, label);
  }
  network = new vis.Network(container, { nodes: nodes, edges: edges }, options);
  network.setOptions({ physics: false });
  network.setOptions({ interaction: { zoomSpeed: user.zoom_sensitivity } });
  for (const objectType of ["Node", "Edge"]) {
    network.on(`hover${objectType}`, function() {
      network.canvas.body.container.style.cursor = "pointer";
    });
    network.on(`blur${objectType}`, function() {
      network.canvas.body.container.style.cursor = "default";
    });
  }
  network.on("select", function() {
    $("#confirmation-builder_deletion").remove();
  });
  network.on("dragStart", () => {
    network.selectNodes(network.getSelectedNodes());
    $("#confirmation-builder_deletion").remove();
  });
  network.on("oncontext", function(properties) {
    if (triggerMenu) {
      properties.event.preventDefault();
      mousePosition = properties.pointer.canvas;
      const node = this.getNodeAt(properties.pointer.DOM);
      const edge = this.getEdgeAt(properties.pointer.DOM);
      if (typeof node !== "undefined" && !ends.has(node)) {
        if (!network.getSelectedNodes().includes(node)) network.selectNodes([node]);
        $(".menu-entry ").hide();
        $(`.${node.length == 36 ? "label" : "node"}-selection`).show();
        selectedObject = nodes.get(node);
        $(`.${instance.type}-selection`).toggle(selectedObject.type == instance.type);
      } else if (typeof edge !== "undefined" && !ends.has(node)) {
        network.selectEdges([edge, ...network.getSelectedEdges()]);
        $(".menu-entry ").hide();
        $(".edge-selection").show();
        selectedObject = edges.get(edge);
      } else {
        $(".menu-entry").hide();
        $(".global").show();
      }
    } else {
      properties.event.stopPropagation();
      properties.event.preventDefault();
    }
  });
  network.on("doubleClick", function(event) {
    mousePosition = event.pointer.canvas;
  });
  if (!$(`#current-${instance.type} option[value='${instance.id}']`).length) {
    const name = instance[type == "workflow" ? "scoped_name" : "name"];
    $(`#current-${instance.type}`).append(
      `<option value="${instance.id}">${name}</option>`
    );
  }
  $(`#current-${instance.type}`)
    .val(instance.id)
    .selectpicker("refresh");
  network.on("dragEnd", (event) => {
    if (network.getNodeAt(event.pointer.DOM)) savePositions();
  });
  rectangleSelection($("#builder"), network, nodes);
  return network;
}

export function drawTree(service, data, resultsPanel) {
  const treeId = service ? `#result-tree-${service}` : `#${type}-tree-${nodeType}s`;
  const noUpdate = builderTreeData == JSON.stringify(data);
  if (!data) {
    builderTreeData = null;
    $(treeId)
      .jstree("destroy")
      .off()
      .empty();
    if (!noUpdate) $(treeId).text("No Results Found.");
    return;
  }
  if (noUpdate && !resultsPanel && $(treeId).children().length > 0) return;
  if ($(treeId).jstree(true) && !resultsPanel) {
    $(treeId).jstree(true).settings.core.data = data;
    $(treeId)
      .jstree(true)
      .refresh();
  } else {
    $(treeId)
      .jstree("destroy")
      .off()
      .empty();
    let tree = $(treeId).jstree({
      core: {
        animation: 100,
        themes: { stripes: true },
        data: data,
      },
      plugins: ["html_row", "types", "wholerow"],
      html_row: {
        default: function(el, node) {
          if (!node) return;
          pidToId[node.data.properties.persistent_id] = node.data.properties.id;
          idToPid[node.data.properties.id] = node.data.properties.persistent_id;
          const runtime = $(
            service ? `#runtimes-tree-${service}` : "#current-runtime"
          ).val();
          const nodeProperties = JSON.stringify(node.data.properties);
          let progressSummary = "";
          const progress = node.data.progress;
          if (progress) {
            const progressList = [
              `<span style="color: #32CD32">${progress.success || 0}${
                resultsPanel ? " passed" : ""
              }</span>`,
              `<span style="color: #FF6666">${progress.failure || 0}${
                resultsPanel ? " failed" : ""
              }</span>`,
            ];
            if (progress.skipped > 0) {
              progressList.splice(
                1,
                0,
                `<span style="color: #7D7D7D">${progress.skipped}${
                  resultsPanel ? " skipped" : ""
                }</span>`
              );
            }
            progressSummary = `
                <div style="position: absolute; top: 0px; right: 160px">
                  ${progressList.join(
                    `<span style="color: #000000">${
                      resultsPanel ? " - " : " / "
                    }</span>`
                  )}
                </div>`;
          }
          const logButton =
            type == "workflow"
              ? `<button type="button"
            class="btn btn-xs btn-primary"
            onclick='eNMS.automation.showRuntimePanel(
              "logs", ${nodeProperties}, "${runtime}"
            )'><span class="glyphicon glyphicon-list"></span>
          </button>`
              : "";
          const resultButton =
            type == "workflow"
              ? `<button type="button"
              class="btn btn-xs btn-primary"
              onclick='eNMS.automation.showRuntimePanel(
                "results", ${nodeProperties}, "${runtime}", "result"
              )'>
              <span class="glyphicon glyphicon-list-alt"></span>
            </button>`
              : `<button type="button"
              class="btn btn-xs btn-primary"
              onclick='eNMS.inventory.showDeviceResultsPanel(${nodeProperties})'>
              <span class="glyphicon glyphicon-list-alt"></span>
            </button>`;
          const buttons = `
            ${logButton}
            ${resultButton}
            <button
              type="button"
              class="btn btn-xs btn-primary"
              data-tooltip="Edit"
              onclick='eNMS.base.showInstancePanel(
                "${node.data.properties.type}", ${node.data.properties.id}
              )'
            >
              <span class="glyphicon glyphicon-edit"></span>
            </button>`;
          $(el)
            .find("a")
            .first().append(`
                ${progressSummary}
                <div style="position: absolute; top: 0px; right: 20px">
                  <button
                    type="button"
                    class="btn btn-xs btn-info"
                    data-tooltip="Find"
                    onclick='eNMS.builder.highlightNode(${JSON.stringify(node.data)})'
                  >
                    <span class="glyphicon glyphicon-screenshot"></span>
                  </button>
                  ${buttons}
                </div>
          `);
        },
      },
      search: {
        show_only_matches: true,
      },
      types: {
        default: {
          icon: "glyphicon glyphicon-file",
        },
        workflow: {
          icon: "fa fa-sitemap fa-rotate-270",
        },
      },
    });
    tree.on("contextmenu", ".jstree-anchor", function(event) {
      const tree = $(treeId).jstree(true);
      selectedObject = tree.get_node(event.target).data.properties;
      $(`.menu-entry,.${type}-selection`).hide();
      $(".node-selection").show();
      if (selectedObject.type !== type) $(`.${type}-selection`).hide();
      if (nodes.get(selectedObject.id)) {
        network.selectNodes([selectedObject.id]);
      } else {
        network.selectNodes([]);
      }
    });
    tree.on("select_node.jstree", function(_, data) {
      network.selectNodes(
        data.selected
          .map((path) => parseInt(path.split(">").pop()))
          .filter((id) => nodes.get(id))
      );
    });
    tree.unbind("dblclick").on("dblclick", function(event) {
      highlightNode(
        $(treeId)
          .jstree(true)
          .get_node(event.target).data
      );
    });
    tree.bind("loaded.jstree", function() {
      createTooltips();
      if (resultsPanel) tree.jstree("open_all");
    });
    $(`#builder,${treeId}`).contextMenu({
      menuSelector: "#contextMenu",
      menuSelected: function(selectedMenu) {
        const row = selectedMenu.text();
        action[row](selectedObject);
      },
    });
  }
  if (!resultsPanel) builderTreeData = JSON.stringify(data);
}

export function highlightNode(node) {
  const nodePath = node.path.split(">").map((pid) => pidToId[pid]);
  const [containerId, nodeId] = nodePath.slice(-2);
  const selection = { nodes: [parseInt(nodeId)], edges: [] };
  if (containerId != instance.id) {
    const listPath = nodePath.length > 1 ? nodePath.slice(0, -1) : nodePath;
    switchTo(listPath.join(">"), null, null, node);
  } else if (nodeId) {
    network.setSelection(selection);
    network.focus(nodeId, {
      scale: 1,
      animation: true,
    });
  }
}

export function savePositions() {
  const positions = network.getPositions();
  call({
    url: `/save_positions/${instance.type}/${instance.id}`,
    data: network.getPositions(),
    callback: function([updateTime, newPositions]) {
      if (updateTime) instance.last_modified = updateTime;
      instance.positions = newPositions;
      nodes.update(
        Object.entries(positions).map(([id, position]) => ({
          id: isNaN(id) ? id : parseInt(id),
          ...position,
        }))
      );
    },
  });
}

export function showBuilderChangelogPanel(model, global) {
  if (global) {
    call({
      url: `/get_builder_children/${model}/${instance.id}`,
      callback: function(children) {
        const subModel = model == "workflow" ? "service" : "device";
        const constraints = {
          [`${subModel}`]: children,
          [`${subModel}_filter`]: "union",
        };
        showChangelogPanel(instance.id, constraints);
      },
    });
  } else {
    const selectedNode = network.getSelectedNodes()[0];
    const classType = model == "workflow" ? "service" : nodes.get(selectedNode).type;
    const serviceName = [nodes.get(selectedNode).full_name]
    showChangelogPanel(instance.id, { [`${classType}`]: serviceName });
  }
}

function showBuilderSearchPanel() {
  const bottomField =
    type == "workflow"
      ? `<div style="width: 100%; margin-bottom: 5px; margin-top: 5px;">
        <fieldset class="custom-fieldset">
          <legend class="custom-legend">Device Filtering</legend>
          <select id="device-filter" name="device-filter" style="width: 100%;"></select>
        </fieldset>
      </div>`
      : "";
  const filteringType = type == "workflow" ? "Service" : "Device";
  openPanel({
    name: "search",
    size: `500 ${type == "workflow" ? "310" : "230"}`,
    content: `
      <form id="search-form-${instance.id}" style="margin: 15px">
        <fieldset class="custom-fieldset">
          <legend class="custom-legend">${filteringType} Filtering</legend>
            <div style="margin-bottom: 5px">
              <select data-width="100%" id="tree-search-mode" name="search_mode">
                <option value="properties">Search across all properties</option>
                <option value="names">Search by service name</option>
              </select>
            </div>
            <input
              type="text"
              id="tree-search"
              name="search_value"
              placeholder="&#xF002;"
              class="form-control"
              style="font-family: Arial, FontAwesome; margin-bottom: 5px"
            />
            <label for="tree-display-all-services">
              <input type="checkbox" id="tree-display-all-services" />
                Include Non-Matching Services in Workflow Tree
            </label>

            <label for="tree-regex-search">
              <input type="checkbox" id="tree-regex-search" />
                Regular Expression Search
            </label>
        </fieldset>
        ${bottomField}
      </form>`,
    id: instance.id,
    title: "Search",
    callback: () => {
      const func = type == "workflow" ? getWorkflowState : getNetworkState;
      initSelect($(`#device-filter`), "device", null, true);
      $("#device-filter,#tree-display-all-services,#tree-regex-search").on(
        "change",
        func
      );
      $("#tree-search-mode")
        .selectpicker()
        .on("change", func);
      let timer = false;
      document.getElementById("tree-search").addEventListener("keyup", function() {
        if (timer) clearTimeout(timer);
        timer = setTimeout(func, 500);
      });
      $(`#search-form-${instance.id}`).on("submit", false);
    },
  });
}

export function showLabelPanel({ label, usePosition }) {
  if (!usePosition) mousePosition = null;
  openPanel({
    name: "label",
    title: label ? "Edit label" : "Create a new label",
    callback: () => {
      if (label) {
        $("#label-text").val(label.label);
        $("#label-size").val(label.font.size);
        $("#label-alignment")
          .val(label.font.align)
          .selectpicker("refresh");
        currentLabel = label;
      } else {
        currentLabel = null;
      }
    },
  });
}

function createLabel() {
  if (!instance) return notify(`No ${type} has been created yet.`, "error", 5);
  const pos = mousePosition ? [mousePosition.x, mousePosition.y] : [0, 0];
  const labelUrl = `${instance.type}/${instance.id}`;
  call({
    url: `/create_label/${labelUrl}/${pos[0]}/${pos[1]}/${currentLabel?.id}`,
    form: "label-form",
    callback: function(result) {
      drawLabel(result.id, result);
      $("#label").remove();
      notify("Label created.", "success", 5);
    },
  });
}

export function drawLabel(id, label) {
  nodes.update({
    id: id,
    shape: "box",
    type: "label",
    font: { align: label.alignment || "center", size: label.size },
    label: label.content,
    borderWidth: 0,
    color: "#FFFFFF",
    x: label.positions[0],
    y: label.positions[1],
  });
}

function deleteSelection() {
  const selection = {
    nodes: network.getSelectedNodes().filter((node) => !ends.has(node)),
    edges: network.getSelectedEdges(),
  };
  selection.nodes.forEach((node) => {
    delete instance.labels[node];
    network.getConnectedEdges(node).forEach((edge) => {
      if (!selection.edges.includes(edge)) selection.edges.push(edge);
    });
  });
  selection.edges = selection.edges.filter((edge) => edge > 0);
  call({
    url: `/delete_builder_selection/${type}/${instance.id}`,
    data: selection,
    callback: function(updateTime) {
      network.deleteSelected();
      network.setSelection({ nodes: [], edges: [] });
      network.interactionHandler.drag.selection = [];
      const edgeType = type == "network" ? "links" : "edges";
      instance[`${nodeType}s`] = instance[`${nodeType}s`].filter(
        (n) => !selection.nodes.includes(n.id)
      );
      instance[edgeType] = instance[edgeType].filter(
        (e) => !selection.edges.includes(e.id)
      );
      instance.last_modified = updateTime;
      notify("Selection removed.", "success", 5);
      switchMode(currentMode, true);
      $("#builder_deletion").remove();
    },
  });
}

function openDeletionPanel() {
  if (!instance) return notify(`No ${type} has been created yet.`, "error", 5);
  const nodes = network.getSelectedNodes();
  const labelSelection = nodes.filter((node) => typeof node === "string").length;
  const nodeSelection = nodes.filter(Number.isInteger).length;
  const edgeSelection = network.getSelectedEdges().length;
  if (!nodeSelection && !edgeSelection && !labelSelection) {
    notify("Nothing has been selected for deletion.", "error", 5);
  } else {
    const edgeType = type == "network" ? "link" : "edge";
    const nodeType = type == "network" ? "device" : "service";
    showConfirmationPanel({
      id: "builder_deletion",
      title: `Deletion from ${type}`,
      message: `Are you sure you want to delete the current selection
      (<b>${nodeSelection} ${nodeType}${nodeSelection > 1 ? "s" : ""},
      ${edgeSelection} ${edgeType}${edgeSelection > 1 ? "s" : ""},
      ${labelSelection} label${labelSelection > 1 ? "s" : ""}</b>) ?`,
      confirmButton: "Delete",
      onConfirm: deleteSelection,
    });
  }
}

function positionNodes(mode, direction) {
  const selectedNodes = network
    .getSelectedNodes()
    .map((id) => nodes.get(id))
    .filter((node) => node.type != "label");
  const length = selectedNodes.length;
  if (mode == "align") {
    const property = direction == "horizontal" ? "y" : "x";
    const value = selectedNodes[0][property];
    selectedNodes.forEach((node) => {
      nodes.update({ id: node.id, [`${property}`]: value });
    });
  } else if (selectedNodes.length > 2) {
    const property = direction == "horizontal" ? "x" : "y";
    selectedNodes.sort((n, m) => n[property] - m[property]);
    const start = selectedNodes[0][property];
    const increment = (selectedNodes[length - 1][property] - start) / (length - 1);
    for (let index = 1; index < length - 1; index++) {
      selectedNodes[index][property] = start + index * increment;
    }
    nodes.update(selectedNodes);
  }
  savePositions();
}

export function updateBuilderBindings(action) {
  Object.assign(action, {
    [`Create ${type}`]: () => createNewNode(`create_${type}`),
    [`Create new ${nodeType}`]: () => createNewNode(`create_${nodeType}`),
    [`Duplicate ${type}`]: () => createNewNode(`duplicate_${type}`),
    [`Edit ${type}`]: () => showInstancePanel(type, instance?.id),
    [`Enter ${type}`]: (node) => switchTo(`${currentPath}>${node.id}`),
    "Create Label": () => showLabelPanel({ usePosition: true }),
    "Create Label Button": () => showLabelPanel({ usePosition: false }),
    "Edit Label": (label) => showLabelPanel({ label: label, usePosition: true }),
    Delete: openDeletionPanel,
    "Horizontal Alignment": () => positionNodes("align", "horizontal"),
    "Vertical Alignment": () => positionNodes("align", "vertical"),
    "Horizontal Distribution": () => positionNodes("distribute", "horizontal"),
    "Vertical Distribution": () => positionNodes("distribute", "vertical"),
    "Zoom In": () => network.zoom(0.2),
    "Zoom Out": () => network.zoom(-0.2),
    Export: () => notify("No workflow found.", "error", 5),
    Backward: () => switchTo(history[historyPosition - 1], "left"),
    Forward: () => switchTo(history[historyPosition + 1], "right"),
    Upward: () => {
      const parentPath = currentPath
        .split(">")
        .slice(0, -1)
        .join(">");
      if (parentPath) switchTo(parentPath);
    },
    Changelog: () => showBuilderChangelogPanel(type),
  });
  $("#builder").contextMenu({
    menuSelector: "#contextMenu",
    menuSelected: function(selectedMenu) {
      const row = selectedMenu.text();
      action[row](selectedObject);
    },
  });
}

export const rectangleSelection = (container, graph, nodes) => {
  const offsetLeft = container.position().left - container.offset().left;
  const offsetTop = container.position().top - container.offset().top;
  let drag = false;
  let DOMRect = {};

  const canvasify = (DOMx, DOMy) => {
    // eslint-disable-next-line new-cap
    const { x, y } = graph.DOMtoCanvas({ x: DOMx, y: DOMy });
    return [x, y];
  };

  const correctRange = (start, end) => (start < end ? [start, end] : [end, start]);

  const selectFromDOMRect = () => {
    const [sX, sY] = canvasify(DOMRect.startX, DOMRect.startY);
    const [eX, eY] = canvasify(DOMRect.endX, DOMRect.endY);
    const [startX, endX] = correctRange(sX, eX);
    const [startY, endY] = correctRange(sY, eY);
    triggerMenu = startX == endX && startY == endY;
    if (triggerMenu) return;
    graph.selectNodes(
      nodes.get().reduce((selected, { id }) => {
        const { x, y } = graph.getPositions(id)[id];
        return startX <= x && x <= endX && startY <= y && y <= endY
          ? selected.concat(id)
          : selected;
      }, [])
    );
  };

  container.on("mousedown", function({ which, pageX, pageY }) {
    const startX = pageX - this.offsetLeft + offsetLeft;
    const startY = pageY - this.offsetTop + offsetTop;
    if (which === 3) {
      Object.assign(DOMRect, {
        startX: startX,
        startY: startY,
        endX: pageX - this.offsetLeft + offsetLeft,
        endY: pageY - this.offsetTop + offsetTop,
      });
      drag = true;
    }
  });

  container.on("mousemove", function({ which, pageX, pageY }) {
    if (which === 0 && drag) {
      drag = false;
      graph.redraw();
    } else if (drag) {
      Object.assign(DOMRect, {
        endX: pageX - this.offsetLeft + offsetLeft,
        endY: pageY - this.offsetTop + offsetTop,
      });
      graph.redraw();
    }
  });

  container.on("mouseup", function({ which }) {
    if (which === 3) {
      drag = false;
      graph.redraw();
      selectFromDOMRect();
    }
  });

  graph.on("afterDrawing", (context) => {
    if (drag) {
      const [startX, startY] = canvasify(DOMRect.startX, DOMRect.startY);
      const [endX, endY] = canvasify(DOMRect.endX, DOMRect.endY);
      context.setLineDash([5]);
      context.strokeStyle = "rgba(78, 146, 237, 0.75)";
      context.strokeRect(startX, startY, endX - startX, endY - startY);
      context.setLineDash([]);
      context.fillStyle = "rgba(151, 194, 252, 0.45)";
      context.fillRect(startX, startY, endX - startX, endY - startY);
    }
  });
};

export function setPath(path) {
  currentPath = path.toString();
}

export function createNewNode(mode) {
  creationMode = mode;
  if (mode == `create_${type}`) {
    showInstancePanel(type);
  } else if (!instance) {
    notify(`No ${type} has been created yet.`, "error", 5);
  } else if (mode == `duplicate_${type}`) {
    showInstancePanel(type, instance.id, "duplicate");
  } else {
    showInstancePanel($(`#${nodeType}-type-dd-list`).val());
  }
}

function drawNode(node) {
  return type == "network" ? drawNetworkNode(node) : drawWorkflowNode(node);
}

function drawEdge(edge) {
  return type == "network" ? drawNetworkEdge(edge) : drawWorkflowEdge(edge);
}

export function switchMode(mode, noNotification) {
  const oldMode = currentMode;
  const newLinkMode = type == "network" ? "create_link" : $("#edge-type-dd-list").val();
  currentMode = mode || (currentMode == "motion" ? newLinkMode : "motion");
  if ((oldMode == "motion" || currentMode == "motion") && oldMode != currentMode) {
    $("#mode-icon")
      .toggleClass("glyphicon-move")
      .toggleClass("glyphicon-random");
  }
  let notification;
  if (!network) return;
  if (currentMode == "motion") {
    network.addNodeMode();
    notification = "Mode: Motion.";
  } else {
    network.setSelection({ nodes: [], edges: [] });
    network.interactionHandler.drag.selection = [];
    network.addEdgeMode();
    const linkLog = type == "network" ? "link" : `'${currentMode}' Edge.`;
    notification = `Mode: Creation of ${linkLog}.`;
  }
  if (!noNotification) notify(notification, "success", 5);
}

export function processBuilderData(newInstance) {
  if (instance) instance.last_modified = newInstance.last_modified;
  if (newInstance.id == instance?.id) {
    instance = newInstance;
    $(`#current-${type} option:selected`)
      .text(newInstance.name)
      .trigger("change");
  }
  if ([`create_${type}`, `duplicate_${type}`].includes(creationMode)) {
    $(`#current-${type}`).append(
      `<option value="${newInstance.id}">${newInstance.name}</option>`
    );
    $(`#current-${type}`)
      .val(newInstance.id)
      .trigger("change");
    creationMode = null;
    switchTo(`${newInstance.id}`);
  } else if (
    (type == "workflow" && newInstance.type == "workflow_edge") ||
    (type == "network" && newInstance.type in subtypes.link)
  ) {
    const property = type == "network" ? "links" : "edges";
    let index = instance[property].findIndex((s) => s.id == newInstance.id);
    if (index == -1) {
      instance[property].push(newInstance);
    } else {
      instance[property][index] = newInstance;
    }
    edges.update(drawEdge(newInstance));
    network.addEdgeMode();
  } else if (
    (type == "workflow" && newInstance.type in subtypes.service) ||
    (type == "network" && newInstance.type in subtypes.device)
  ) {
    if (!newInstance[`${type}s`].some((w) => w.id == instance.id)) return;
    const property = type == "network" ? "devices" : "services";
    let index = instance[property].findIndex((s) => s.id == newInstance.id);
    if (index == -1) {
      instance[property].push(newInstance);
    } else {
      const oldRecordName = instance[property][index].name;
      instance.positions[newInstance.name] = instance.positions[oldRecordName];
      instance[property][index] = newInstance;
    }
    nodes.update(drawNode(newInstance));
    if (type == "workflow") drawIterationEdge(instance);
    switchMode("motion");
  }
}

function switchTo(...args) {
  (type == "network" ? switchToNetwork : switchToWorkflow)(...args);
}

function updateRightClickBindings() {
  (type == "network"
    ? updateNetworkRightClickBindings
    : updateWorkflowRightClickBindings)();
}

export function initBuilder() {
  vis.Network.prototype.zoom = function(scale) {
    const animationOptions = {
      scale: this.getScale() + scale,
      animation: { duration: 300 },
    };
    this.view.moveTo(animationOptions);
  };
  $("#edge-type-dd-list")
    .selectpicker()
    .on("change", function() {
      switchMode(this.value);
    });
  if (type == "network") {
    loadTypes("device");
    loadTypes("edge");
  } else {
    loadTypes("service");
    flipRuntimeDisplay(runtimeDisplay);
  }
  $("#left-arrow,#right-arrow").addClass("disabled");
  call({
    url: `/get_top_level_instances/${type}`,
    callback: function(result) {
      const instanceIds = new Set();
      if (result.Other && Object.keys(result).length == 1) {
        const instances = result.Other.sort((a, b) => a.name.localeCompare(b.name));
        for (let i = 0; i < instances.length; i++) {
          instanceIds.add(instances[i].id.toString());
          $(`#current-${type}`).append(
            `<option value="${instances[i].id}">${instances[i].name}</option>`
          );
        }
      } else {
        for (const [category, instances] of Object.entries(result)) {
          $(`#current-${type}`).append(`<optgroup label="${category}">`);
          const sortedInstances = instances.sort((a, b) =>
            a.name.localeCompare(b.name)
          );
          sortedInstances.forEach((instance) => {
            instanceIds.add(instance.id.toString());
            $(`#current-${type} optgroup[label="${category}"]`).append(
              `<option value="${instance.id}">${instance.name}</option>`
            );
          });
        }
      }
      if (currentPath && instanceIds.has(currentPath.split(">")[0])) {
        $(`#current-${type}`).val(currentPath.split(">")[0]);
        switchTo(currentPath);
      } else {
        instance = $(`#current-${type}`).val();
        if (instance) {
          switchTo(instance);
        } else {
          notify(`No ${type} has been created yet.`, "error", 5);
        }
      }
      $(`#current-${type},#current-runtime`).selectpicker({
        liveSearch: true,
        virtualScroll: false
      });
      if (type == "workflow") {
        $("#current-runtime").on("change", function() {
          getWorkflowState();
        });
        getWorkflowState(true, true);
      } else {
        getNetworkState(true, true);
      }
    },
  });
  $(`#current-${type}`).on("change", function() {
    if (!instance || this.value != instance.id) switchTo(this.value);
  });
  updateRightClickBindings();
}

function toggleTree() {
  const kwargs = { duration: 200, queue: false };
  if (!treeIsDisplayed) {
    $(`#${type}-tree,#resize-tree-li`).show();
    $("#run-navbar").hide();
    $(".left_frame").animate({ width: "-=600px" }, kwargs);
    $(".right_frame").animate(
      { width: "600px" },
      {
        ...kwargs,
        complete: () => {
          $("#run-navbar")
            .appendTo(`#${type}-tree-control`)
            .show();
          (type == "workflow" ? getWorkflowState : getNetworkState)();
        },
      }
    );
  } else {
    $("#run-navbar,#resize-tree-li").hide();
    $(".left_frame").animate({ width: "+=600px" }, kwargs);
    $(".right_frame").animate(
      { width: "-=600px" },
      {
        ...kwargs,
        complete: () => {
          $("#run-navbar")
            .appendTo(`#${type}-controls`)
            .show();
          $(`#${type}-tree`).hide();
        },
      }
    );
  }
  $(`#${type}-tree-btn`).toggleClass("active");
  treeIsDisplayed = !treeIsDisplayed;
  call({
    url: "/save_profile",
    data: { id: user.id, display_tree: treeIsDisplayed },
  });
}

configureNamespace("builder", [
  createLabel,
  highlightNode,
  showBuilderSearchPanel,
  switchMode,
  toggleTree,
]);
