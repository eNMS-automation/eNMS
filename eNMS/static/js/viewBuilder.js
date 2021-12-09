/*
global
action: false
page: false
*/

import {
  call,
  history,
  historyPosition,
  moveHistory,
  notify,
  showInstancePanel,
} from "./base.js";
import { rectangleSelection, triggerMenu } from "./builder.js";

let ctrlKeyPressed;
let currentView;
let graph;
let edges;
let nodes;
export let currentPath = localStorage.getItem("path");
export let view = JSON.parse(localStorage.getItem("view"));

const container = document.getElementById("network");
const options = {
  interaction: {
    hover: true,
    hoverConnectedEdges: false,
    multiselect: true,
  },
  manipulation: {
    enabled: false,
    addNode: function (data, callback) {},
    addEdge: function (data, callback) {},
    deleteNode: function (data, callback) {
      callback(data);
    },
  },
};

function switchToView(path, direction) {
  if (typeof path === "undefined") return;
  if (path.toString().includes(">")) {
    $("#up-arrow").removeClass("disabled");
  } else {
    $("#up-arrow").addClass("disabled");
  }
  currentPath = path;
  localStorage.setItem(page, currentPath);
  moveHistory(path, direction);
  const [viewId] = currentPath.split(">").slice(-1);
  if (!path && page == "object_table") {
    $("#view-filtering").val("");
    tableInstances["object"].table.page(0).ajax.reload(null, false);
    return;
  }
  call({
    url: `/get/view/${viewId}`,
    callback: function (view) {
      currentView = view;
      if (page == "view_builder") {
        if (view) localStorage.setItem("view", JSON.stringify(view));
        displayView(view);
      } else {
        $("#view-filtering").val(path ? view.name : "");
        tableInstances["object"].table.page(0).ajax.reload(null, false);
      }
    },
  });
};

export function displayView(view) {
  nodes = new vis.DataSet([]);
  edges = new vis.DataSet([]);
  for (const [id, label] of Object.entries(view.labels)) {
    drawLabel(id, label);
  }
  graph = new vis.Network(container, { nodes: nodes, edges: edges }, options);
  graph.setOptions({ physics: false });
  graph.on("oncontext", function (properties) {
    if (triggerMenu) {
      // eslint-disable-next-line new-cap
      mousePosition = properties.pointer.canvas;
      properties.event.preventDefault();
      const node = this.getNodeAt(properties.pointer.DOM);
      const edge = this.getEdgeAt(properties.pointer.DOM);
      if (typeof node !== "undefined" && !ends.has(node)) {
        graph.selectNodes([node, ...graph.getSelectedNodes()]);
        $(".menu-entry ").hide();
        $(`.${node.length == 36 ? "label" : "node"}-selection`).show();
        selectedObject = nodes.get(node);
        $(".view-selection").toggle(selectedObject.type == "view");
      } else if (typeof edge !== "undefined" && !ends.has(node)) {
        graph.selectEdges([edge, ...graph.getSelectedEdges()]);
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
  graph.on("click", () => {
    if (!ctrlKeyPressed) graph.selectNodes([]);
  });
  graph.on("doubleClick", function (event) {
    mousePosition = event.pointer.canvas;
    event.event.preventDefault();
    let node = nodes.get(this.getNodeAt(event.pointer.DOM));
    if (!node || !node.id) {
      return;
    } else if (node.type == "label") {
      showLabelPanel({ label: node, usePosition: true });
    } else if (node.type == "view") {
      switchToView(`${currentPath}>${node.id}`);
    } else {
      showInstancePanel(node.type, node.id);
    }
  });
  for (const objectType of ["Node", "Edge"]) {
    graph.on(`hover${objectType}`, function () {
      graph.canvas.body.container.style.cursor = "pointer";
    });
    graph.on(`blur${objectType}`, function () {
      graph.canvas.body.container.style.cursor = "default";
    });
  }
  if (!$(`#current-view option[value='${view.id}']`).length) {
    $("#current-view").append(
      `<option value="${view.id}">${view.scoped_name}</option>`
    );
  }
  $("#current-view").val(view.id).selectpicker("refresh");
  graph.on("dragEnd", (event) => {
    if (graph.getNodeAt(event.pointer.DOM)) savePositions();
  });
  rectangleSelection($("#network"), graph, nodes);
}

function createNewView(mode) {
  if (mode == "create_view") {
    showInstancePanel("view");
  } else if (!currentView) {
    notify("No view has been created yet.", "error", 5);
  } else if (mode == "duplicate_view") {
    showInstancePanel("view", currentView.id, "duplicate");
  } else {
    showInstancePanel("view", currentView.id);
  }
}

function openDeletionPanel() {}

function updateRightClickBindings() {
  Object.assign(action, {
    "Create View": () => createNewView("create_view"),
    "Duplicate View": () => createNewView("duplicate_view"),
    "Edit View": () => showInstancePanel("view", currentView.id),
    Delete: openDeletionPanel,
    "Create Label": () => showLabelPanel({ usePosition: true }),
    "Create Label Button": () => showLabelPanel({ usePosition: false }),
    "Edit Label": (label) => showLabelPanel({ label: label, usePosition: true }),
    "Edit Edge": (edge) => {
      showInstancePanel("link", edge.id);
    },
    Skip: () => skipServices(),
    "Zoom In": () => graph.zoom(0.2),
    "Zoom Out": () => graph.zoom(-0.2),
    "Enter View": (node) => switchToView(`${currentPath}>${node.id}`),
    Backward: () => switchToView(history[historyPosition - 1], "left"),
    Forward: () => switchToView(history[historyPosition + 1], "right"),
    Upward: () => {
      const parentPath = currentPath.split(">").slice(0, -1).join(">");
      if (parentPath) switchToView(parentPath);
    },
  });
  $("#network").contextMenu({
    menuSelector: "#contextMenu",
    menuSelected: function (selectedMenu) {
      const row = selectedMenu.text();
      action[row](selectedObject);
    },
  });
}

export function initViewBuilder() {
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
  $("#left-arrow,#right-arrow").addClass("disabled");
  call({
    url: "/get_top_level_instances/view",
    callback: function (views) {
      views.sort((a, b) => a.name.localeCompare(b.name));
      for (let i = 0; i < views.length; i++) {
        $("#current-view").append(
          `<option value="${views[i].id}">${views[i].name}</option>`
        );
      }
      if (currentPath && views.some((w) => w.id == currentPath.split(">")[0])) {
        $("#current-view").val(currentPath.split(">")[0]);
        switchToView(currentPath);
      } else {
        view = $("#current-view").val();
        if (view) {
          switchToView(view);
        } else {
          notify("No view has been created yet.", "error", 5);
        }
      }
      $("#current-view").selectpicker({ liveSearch: true });
    },
  });
  $("#current-view").on("change", function () {
    if (!view || this.value != view.id) switchToView(this.value);
  });
  updateRightClickBindings();
}

export function viewCreation(instance) {
  if (instance.id == currentView?.id) {
    $("#current-view option:selected").text(instance.name).trigger("change");
  } else {
    $("#current-view").append(
      `<option value="${instance.id}">${instance.name}</option>`
    );
    $("#current-view").val(instance.id).trigger("change");
    displayView(instance);
  }
}
