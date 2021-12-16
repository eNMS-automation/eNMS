import { call, configureNamespace,   history,
  historyPosition, loadTypes, notify, openPanel } from "./base.js";
import { switchToSite } from "./siteBuilder.js";

const container = document.getElementById("network");
let currentLabel;
let instance;
let mousePosition;
let network;
let selectedObject;
export let currentPath = localStorage.getItem("path");
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
  for (const objectType of ["Node", "Edge"]) {
    network.on(`hover${objectType}`, function () {
      network.canvas.body.container.style.cursor = "pointer";
    });
    network.on(`blur${objectType}`, function () {
      network.canvas.body.container.style.cursor = "default";
    });
  }
  network.on("oncontext", function (properties) {
    if (triggerMenu) {
      properties.event.preventDefault();
      mousePosition = properties.pointer.canvas;
      const node = this.getNodeAt(properties.pointer.DOM);
      const edge = this.getEdgeAt(properties.pointer.DOM);
      if (typeof node !== "undefined" && !graph.inactive.has(node)) {
        network.selectNodes([node, ...network.getSelectedNodes()]);
        $(".menu-entry ").hide();
        $(`.${node.length == 36 ? "label" : "node"}-selection`).show();
        selectedObject = nodes.get(node);
        $(`.${instance.type}-selection`).toggle(selectedObject.type == instance.type);
      } else if (typeof edge !== "undefined" && !graph.inactive.has(node)) {
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
    $(`#current-${instance.type}`).append(
      `<option value="${instance.id}">${instance.scoped_name}</option>`
    );
  }
  $(`#current-${instance.type}`).val(instance.id).selectpicker("refresh");
  network.on("dragEnd", (event) => {
    if (network.getNodeAt(event.pointer.DOM)) savePositions();
  });
  rectangleSelection($("#network"), network, nodes);
  return network;
}

function savePositions() {
  call({
    url: `/save_positions/${instance.type}/${instance.id}`,
    data: network.getPositions(),
    callback: function (updateTime) {
      if (updateTime) instance.last_modified = updateTime;
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
        $("#label-alignment").val(label.font.align).selectpicker("refresh");
        currentLabel = label;
      } else {
        currentLabel = null;
      }
    },
  });
}

function createLabel() {
  const pos = mousePosition ? [mousePosition.x, mousePosition.y] : [0, 0];
  const instance = `${instance.type}/${instance.id}`;
  call({
    url: `/create_label/${instance}/${pos[0]}/${pos[1]}/${currentLabel?.id}`,
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
    font: { align: label.alignment || "center" },
    label: label.content,
    borderWidth: 0,
    color: "#FFFFFF",
    x: label.positions[0],
    y: label.positions[1],
  });
}

export function updateBuilderBindings(action) {
  Object.assign(action, {
    "Create Label": () => showLabelPanel({ usePosition: true }),
    "Create Label Button": () => showLabelPanel({ usePosition: false }),
    "Edit Label": (label) => showLabelPanel({ label: label, usePosition: true }),
  });
  $("#network").contextMenu({
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

export function updateSiteRightClickBindings() {
  updateBuilderBindings(action);
  Object.assign(action, {
    "Create Site": () => createNewNode("create_site"),
    "Duplicate Site": () => createNewNode("duplicate_site"),
    "Create New Node": () => createNewNode("create_node"),
    "Edit Site": () => showInstancePanel("site", site?.id),
    "Edit Edge": (edge) => showInstancePanel(edge.type, edge.id),
    "Zoom In": () => graph.zoom(0.2),
    "Zoom Out": () => graph.zoom(-0.2),
    "Enter Site": (node) => switchToSite(`${currentPath}>${node.id}`),
    "Site Backward": () => switchToSite(history[historyPosition - 1], "left"),
    "Site Forward": () => switchToSite(history[historyPosition + 1], "right"),
    "Site Upward": () => {
      const parentPath = currentPath.split(">").slice(0, -1).join(">");
      if (parentPath) switchToSite(parentPath);
    },
  });
}

export function initBuilder() {
  window.onkeydown = () => {
    ctrlKeyPressed = true;
  };
  window.onkeyup = () => {
    ctrlKeyPressed = false;
  };
  vis.Network.prototype.zoom = function (scale) {
    const animationOptions = {
      scale: this.getScale() + scale,
      animation: { duration: 300 },
    };
    this.view.moveTo(animationOptions);
  };
  loadTypes("node");
  loadTypes("link");
  $("#left-arrow,#right-arrow").addClass("disabled");
  call({
    url: "/get_top_level_instances/site",
    callback: function (sites) {
      sites.sort((a, b) => a.name.localeCompare(b.name));
      for (let i = 0; i < sites.length; i++) {
        $("#current-site").append(
          `<option value="${sites[i].id}">${sites[i].name}</option>`
        );
      }
      if (currentPath && sites.some((w) => w.id == currentPath.split(">")[0])) {
        $("#current-site").val(currentPath.split(">")[0]);
        switchToSite(currentPath);
      } else {
        site = $("#current-site").val();
        if (site) {
          switchToSite(site);
        } else {
          notify("No site has been created yet.", "error", 5);
        }
      }
      $("#current-site").selectpicker({ liveSearch: true });
    },
  });
  $("#current-site").on("change", function () {
    if (!site || this.value != site.id) switchToSite(this.value);
  });
  updateSiteRightClickBindings();
}

configureNamespace("builder", [createLabel]);
