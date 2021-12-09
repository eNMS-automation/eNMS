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
let currentSite;
let graph;
let edges;
let nodes;
export let currentPath = localStorage.getItem("path");
export let site = JSON.parse(localStorage.getItem("site"));

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

function switchToSite(path, direction) {
  if (typeof path === "undefined") return;
  if (path.toString().includes(">")) {
    $("#up-arrow").removeClass("disabled");
  } else {
    $("#up-arrow").addClass("disabled");
  }
  currentPath = path;
  localStorage.setItem(page, currentPath);
  moveHistory(path, direction);
  const [siteId] = currentPath.split(">").slice(-1);
  if (!path && page == "object_table") {
    $("#site-filtering").val("");
    tableInstances["object"].table.page(0).ajax.reload(null, false);
    return;
  }
  call({
    url: `/get/site/${siteId}`,
    callback: function (site) {
      currentSite = site;
      if (page == "site_builder") {
        if (site) localStorage.setItem("site", JSON.stringify(site));
        displaySite(site);
      } else {
        $("#site-filtering").val(path ? site.name : "");
        tableInstances["object"].table.page(0).ajax.reload(null, false);
      }
    },
  });
};

export function displaySite(site) {
  nodes = new vis.DataSet([]);
  edges = new vis.DataSet([]);
  for (const [id, label] of Object.entries(site.labels)) {
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
        $(".site-selection").toggle(selectedObject.type == "site");
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
    event.event.preventDefault();
    let node = nodes.get(this.getNodeAt(event.pointer.DOM));
    if (!node || !node.id) {
      return;
    } else if (node.type == "label") {
      showLabelPanel({ label: node, usePosition: true });
    } else if (node.type == "site") {
      switchToSite(`${currentPath}>${node.id}`);
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
  if (!$(`#current-site option[value='${site.id}']`).length) {
    $("#current-site").append(
      `<option value="${site.id}">${site.scoped_name}</option>`
    );
  }
  $("#current-site").val(site.id).selectpicker("refresh");
  graph.on("dragEnd", (event) => {
    if (graph.getNodeAt(event.pointer.DOM)) savePositions();
  });
  rectangleSelection($("#network"), graph, nodes);
}

function createNewSite(mode) {
  if (mode == "create_site") {
    showInstancePanel("site");
  } else if (!currentSite) {
    notify("No site has been created yet.", "error", 5);
  } else if (mode == "duplicate_site") {
    showInstancePanel("site", currentSite.id, "duplicate");
  } else {
    showInstancePanel("site", currentSite.id);
  }
}

function openDeletionPanel() {}

function updateRightClickBindings() {
  Object.assign(action, {
    "Create Site": () => createNewSite("create_site"),
    "Duplicate Site": () => createNewSite("duplicate_site"),
    "Edit Site": () => showInstancePanel("site", currentSite.id),
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
    "Enter Site": (node) => switchToSite(`${currentPath}>${node.id}`),
    Backward: () => switchToSite(history[historyPosition - 1], "left"),
    Forward: () => switchToSite(history[historyPosition + 1], "right"),
    Upward: () => {
      const parentPath = currentPath.split(">").slice(0, -1).join(">");
      if (parentPath) switchToSite(parentPath);
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

export function initSiteBuilder() {
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
  updateRightClickBindings();
}

export function siteCreation(instance) {
  if (instance.id == currentSite?.id) {
    $("#current-site option:selected").text(instance.name).trigger("change");
  } else {
    $("#current-site").append(
      `<option value="${instance.id}">${instance.name}</option>`
    );
    $("#current-site").val(instance.id).trigger("change");
    displaySite(instance);
  }
}
