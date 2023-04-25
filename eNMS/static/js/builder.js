/*
global
linkPath: false
page: false
subtypes: false
vis: false
*/

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
  showConfirmationPanel,
  showInstancePanel,
} from "./base.js";
import {
  drawNetworkEdge,
  drawNetworkNode,
  getNetworkState,
  resetNetworkDisplay,
  switchToNetwork,
  updateNetworkRightClickBindings,
} from "./networkBuilder.js";
import {
  colorService,
  drawIterationEdge,
  drawWorkflowEdge,
  drawWorkflowNode,
  ends,
  flipRuntimeDisplay,
  getWorkflowState,
  resetWorkflowDisplay,
  switchToWorkflow,
  updateWorkflowRightClickBindings,
} from "./workflowBuilder.js";

const container = document.getElementById("builder");
const type = page.includes("network") ? "network" : "workflow";
const nodeType = type == "network" ? "node" : "service";
const savedPath = linkPath || localStorage.getItem(`${type}_path`);
let currentLabel;
let mousePosition;
let network;
let selectedObject;
export let creationMode;
export let currentMode = "motion";
export let currentPath = page.includes("builder") && savedPath;
export let instance;
export let edges;
export let nodes;
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
  network.setOptions({ interaction: { zoomSpeed: user.zoom_sensitivity }});
  for (const objectType of ["Node", "Edge"]) {
    network.on(`hover${objectType}`, function () {
      network.canvas.body.container.style.cursor = "pointer";
    });
    network.on(`blur${objectType}`, function () {
      network.canvas.body.container.style.cursor = "default";
    });
  }
  network.on("select", function () {
    $("#confirmation-builder_deletion").remove();
  });
  network.on("dragStart", () => {
    $("#confirmation-builder_deletion").remove();
  });
  network.on("oncontext", function (properties) {
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
  network.on("doubleClick", function (event) {
    mousePosition = event.pointer.canvas;
  });
  if (!$(`#current-${instance.type} option[value='${instance.id}']`).length) {
    const name = instance[type == "workflow" ? "scoped_name" : "name"];
    $(`#current-${instance.type}`).append(
      `<option value="${instance.id}">${name}</option>`
    );
  }
  $(`#current-${instance.type}`).val(instance.id).selectpicker("refresh");
  network.on("dragEnd", (event) => {
    if (network.getNodeAt(event.pointer.DOM)) savePositions();
  });
  rectangleSelection($("#builder"), network, nodes);
  return network;
}

function highlightNode(node) {
  const nodePath = node.path.split(">");
  const [containerId, nodeId] = nodePath.slice(-2);
  const selection = { nodes: [parseInt(nodeId)], edges: [] };
  if (containerId != instance.id) {
    switchTo(nodePath.slice(0, -1).join(">"), null, null, selection);
  } else if (nodeId) {
    network.setSelection(selection);
  }
}

export function savePositions() {
  const positions = network.getPositions();
  call({
    url: `/save_positions/${instance.type}/${instance.id}`,
    data: network.getPositions(),
    callback: function (updateTime) {
      if (updateTime) instance.last_modified = updateTime;
      nodes.update(
        Object.entries(positions).map(([id, position]) => ({
          id: isNaN(id) ? id : parseInt(id),
          ...position,
        }))
      );
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
        $("#label-alignment").val(label.font.align).selectpicker("refresh");
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
    callback: function (result) {
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
    callback: function (updateTime) {
      network.deleteSelected();
      network.setSelection({ nodes: [], edges: [] });
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
  const nodeSelection = network.getSelectedNodes().length;
  const edgeSelection = network.getSelectedEdges().length;
  if (!nodeSelection && !edgeSelection) {
    notify("Nothing has been selected for deletion.", "error", 5);
  } else {
    const edgeType = type == "network" ? "link" : "edge";
    showConfirmationPanel({
      id: "builder_deletion",
      title: `Deletion from ${type}`,
      message: `Are you sure you want to permanently remove the current selection
      (<b>${nodeSelection} node${nodeSelection > 1 ? "s" : ""}
      and ${edgeSelection} ${edgeType}${edgeSelection > 1 ? "s" : ""}</b>) ?`,
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
      const parentPath = currentPath.split(">").slice(0, -1).join(">");
      if (parentPath) switchTo(parentPath);
    },
  });
  $("#builder").contextMenu({
    menuSelector: "#contextMenu",
    menuSelected: function (selectedMenu) {
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

  container.on("mousedown", function ({ which, pageX, pageY }) {
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

  container.on("mousemove", function ({ which, pageX, pageY }) {
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

  container.on("mouseup", function ({ which }) {
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
  currentPath = path;
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
    showInstancePanel($(`#${nodeType}-type-list`).val());
  }
}

function displayTextSearchField() {
  $(`#${type}-search-div`).toggle();
  if ($(`#${type}-search-div`).is(":visible")) {
    $(`#${type}-search`).focus();
  } else {
    $(`#${type}-search`).val("");
    if (type == "workflow") {
      getWorkflowState();
    } else {
      resetNetworkDisplay();
      getNetworkState();
    }
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
  const newLinkMode = type == "network" ? "create_link" : $("#edge-type-list").val();
  currentMode = mode || (currentMode == "motion" ? newLinkMode : "motion");
  if ((oldMode == "motion" || currentMode == "motion") && oldMode != currentMode) {
    $("#mode-icon").toggleClass("glyphicon-move").toggleClass("glyphicon-random");
  }
  let notification;
  if (currentMode == "motion") {
    network.addNodeMode();
    notification = "Mode: Motion.";
  } else {
    network.setSelection({ nodes: [], edges: [] });
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
    $(`#current-${type} option:selected`).text(newInstance.name).trigger("change");
  }
  if ([`create_${type}`, `duplicate_${type}`].includes(creationMode)) {
    $(`#current-${type}`).append(
      `<option value="${newInstance.id}">${newInstance.name}</option>`
    );
    $(`#current-${type}`).val(newInstance.id).trigger("change");
    creationMode = null;
    switchTo(`${newInstance.id}`);
  } else if (
    (type == "workflow" && !instance.type) ||
    (type == "network" && newInstance.type in subtypes.link)
  ) {
    edges.update(drawEdge(newInstance));
    network.addEdgeMode();
  } else if (
    (type == "workflow" && newInstance.type in subtypes.service) ||
    (type == "network" && newInstance.type in subtypes.node)
  ) {
    if (!newInstance[`${type}s`].some((w) => w.id == instance.id)) return;
    const property = type == "network" ? "nodes" : "services";
    let index = instance[property].findIndex((s) => s.id == newInstance.id);
    nodes.update(drawNode(newInstance));
    if (index == -1) {
      instance[property].push(newInstance);
    } else {
      instance[property][index] = newInstance;
    }
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
  vis.Network.prototype.zoom = function (scale) {
    const animationOptions = {
      scale: this.getScale() + scale,
      animation: { duration: 300 },
    };
    this.view.moveTo(animationOptions);
  };
  $("#edge-type-list")
    .selectpicker()
    .on("change", function () {
      switchMode(this.value);
    });
  if (type == "network") {
    loadTypes("node");
    loadTypes("edge");
  } else {
    loadTypes("service");
    flipRuntimeDisplay(localStorage.getItem("runtimeDisplay") || "user");
  }
  $("#left-arrow,#right-arrow").addClass("disabled");
  call({
    url: `/get_top_level_instances/${type}`,
    callback: function (result) {
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
      $(`#current-${type},#current-runtimes`).selectpicker({ liveSearch: true });
      let searchTimer = false;
      $(`#${type}-search`).keyup(function () {
        if (searchTimer) clearTimeout(searchTimer);
        searchTimer = setTimeout(searchBuilderText, 300);
      });
      if (type == "workflow") {
        initSelect($(`#device-filter`), "device", null, true);
        $("#current-runtime,#device-filter").on("change", function () {
          getWorkflowState();
        });
        getWorkflowState(true, true);
      } else {
        getNetworkState(true, true);
      }
    },
  });
  $(`#current-${type}`).on("change", function () {
    if (!instance || this.value != instance.id) switchTo(this.value);
  });
  updateRightClickBindings();
}

export function searchBuilderText() {
  const searchValue = $(`#${type}-search`).val();
  if (!searchValue) return;
  call({
    url: `/search_builder/${type}/${instance.id}/${searchValue}`,
    callback: function (selectedNodes) {
      if (type == "workflow") {
        resetWorkflowDisplay();
        selectedNodes.forEach((node) => colorService(node, "#EFFD5F"));
      } else {
        resetNetworkDisplay();
        selectedNodes.forEach((nodeId) => {
          const icon = nodes.get(parseInt(nodeId)).icon;
          const image = `/static/img/network/red/${icon}.gif`;
          nodes.update({ id: parseInt(nodeId), image: image });
        });
      }
    },
  });
}

function getTree() {
  if (!instance) return notify(`No ${type} has been created yet.`, "error", 5);
  const instanceId = instance.id;
  openPanel({
    name: "instance_tree",
    title: `${instance.name} - Tree Structure`,
    content: `
      <div class="modal-body">
        <input
          type="text"
          class="form-control"
          id="tree-search-${instanceId}"
          placeholder="Search"
        >
        <hr />
        <div id="instance-tree-${instanceId}"></div>
        <input type="hidden" name="services" id="services" />
      </div>`,
    callback: function () {
      call({
        url: `/get_instance_tree/${type}/${currentPath}`,
        callback: function (data) {
          $(`#instance-tree-${instanceId}`)
            .bind("loaded.jstree", function (e, data) {
              createTooltips();
            })
            .jstree({
              core: {
                animation: 100,
                themes: { stripes: true },
                data: data,
              },
              plugins: ["html_row", "search", "types", "wholerow"],
              html_row: {
                default: function (el, node) {
                  if (!node) return;
                  $(el).find("a").first().append(`
                  <div style="position: absolute; top: 0px; right: 20px">
                    <button
                      type="button"
                      class="btn btn-xs btn-info"
                      data-tooltip="Find"
                      onclick='eNMS.builder.highlightNode(${JSON.stringify(node.data)})'
                    >
                      <span class="glyphicon glyphicon-screenshot"></span>
                    </button>
                    <button
                      type="button"
                      class="btn btn-xs btn-primary"
                      data-tooltip="Edit"
                      onclick='eNMS.base.showInstancePanel(
                        "${node.data.type}", ${node.data.id}
                      )'
                    >
                      <span class="glyphicon glyphicon-edit"></span>
                    </button>
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
                  icon: "fa fa-sitemap",
                },
              },
            });
          let timer = false;
          $(`#tree-search-${instanceId}`).keyup(function () {
            if (timer) clearTimeout(timer);
            timer = setTimeout(function () {
              const searchValue = $(`#tree-search-${instanceId}`).val();
              $(`#instance-tree-${instanceId}`).jstree(true).search(searchValue);
            }, 500);
          });
        },
      });
    },
  });
}

configureNamespace("builder", [
  createLabel,
  displayTextSearchField,
  getTree,
  highlightNode,
  switchMode,
]);
