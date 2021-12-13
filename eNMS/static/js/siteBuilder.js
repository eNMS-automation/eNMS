/*
global
action: false
page: false
*/

import {
  call,
  history,
  historyPosition,
  loadTypes,
  moveHistory,
  notify,
  showInstancePanel,
} from "./base.js";
import {
  configureGraph,
  nodes,
  showLabelPanel,
  updateBuilderBindings,
} from "./builder.js";

let creationMode;
let currentMode;
let ctrlKeyPressed;
let graph;
export let currentPath = localStorage.getItem("path");
export let site = JSON.parse(localStorage.getItem("site"));

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
    callback: function (newSite) {
      site = newSite;
      if (page == "site_builder") {
        if (site) localStorage.setItem("site", JSON.stringify(site));
        displaySite(site);
      } else {
        $("#site-filtering").val(path ? site.name : "");
        tableInstances["object"].table.page(0).ajax.reload(null, false);
      }
    },
  });
}

export function displaySite(site) {
  graph = configureGraph(
    site,
    {
      nodes: site.nodes.map(drawNode),
      edges: [],
      inactive: [],
    },
    options
  );
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
}

function drawNode(node) {
  return {
    id: node.id,
    shape: "box",
    color: "#D2E5FF",
    font: {
      size: 15,
      multi: "html",
      align: "center",
      bold: { color: "#000000" },
    },
    shadow: {
      enabled: true,
      color: node.shared ? "#FF1694" : "#6666FF",
      size: 15,
    },
    label: node.scoped_name,
    name: node.name,
    type: node.type,
    image: `/static/img/view/2D/router.gif`,
    shape: "image",
    x: node.positions[site.name] ? node.positions[site.name][0] : 0,
    y: node.positions[site.name] ? node.positions[site.name][1] : 0,
  };
}

function drawLine() {
  return {}
}

export function updateSitePanel() {
  if (creationMode == "create_node") {
    $(`#node-sites`).append(new Option(site.name, site.name));
    $(`#node-sites`).val(site.name).trigger("change");
  }
}

function createNewNode(mode) {
  creationMode = mode;
  if (mode == "create_site") {
    showInstancePanel("site");
  } else if (!site) {
    notify("No site has been created yet.", "error", 5);
  } else if (mode == "duplicate_site") {
    showInstancePanel("site", site.id, "duplicate");
  } else {
    showInstancePanel("node");
  }
}

function openDeletionPanel() {}

function updateRightClickBindings() {
  updateBuilderBindings(action);
  Object.assign(action, {
    "Create Site": () => createNewNode("create_site"),
    "Duplicate Site": () => createNewNode("duplicate_site"),
    "Create New Node": () => createNewNode("create_node"),
    "Edit Site": () => showInstancePanel("site", site.id),
    Delete: openDeletionPanel,
    "Edit Edge": (edge) => {
      showInstancePanel("link", edge.id);
    },
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
  loadTypes("node");
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
  if (instance.id == site?.id) {
    $("#current-site option:selected").text(instance.name).trigger("change");
  } else {
    $("#current-site").append(
      `<option value="${instance.id}">${instance.name}</option>`
    );
    $("#current-site").val(instance.id).trigger("change");
    displaySite(instance);
  }
}

function switchMode(mode, noNotification) {
  const oldMode = currentMode;
  currentMode = mode || (currentMode == "motion" ? $("#edge-type").val() : "motion");
  if ((oldMode == "motion" || currentMode == "motion") && oldMode != currentMode) {
    $("#mode-icon").toggleClass("glyphicon-move").toggleClass("glyphicon-random");
  }
  let notification;
  if (currentMode == "motion") {
    graph.addNodeMode();
    notification = "Mode: Motion.";
  } else {
    graph.setSelection({ nodes: [], edges: [] });
    graph.addEdgeMode();
    notification = "Mode: Creation of link.";
  }
  if (!noNotification) notify(notification, "success", 5);
}

export function processSiteData(instance) {
  if (instance.id == site?.id) {
    site = instance;
    $("#current-site option:selected").text(instance.name).trigger("change");
  }
  if (["create_site", "duplicate_site"].includes(creationMode)) {
    $("#current-site").append(
      `<option value="${instance.id}">${instance.name}</option>`
    );
    $("#current-site").val(instance.id).trigger("change");
    creationMode = null;
    switchToSite(`${instance.id}`);
  } else if (!instance.type) {
    edges.update(edgeToEdge(instance));
  } else if (["node", "site"].includes(instance.type)) {
    if (!instance.sites.some((w) => w.id == site.id)) return;
    let serviceIndex = site.nodes.findIndex((s) => s.id == instance.id);
    nodes.update(drawNode(instance));
    if (serviceIndex == -1) {
      site.nodes.push(instance);
    } else {
      site.nodes[serviceIndex] = instance;
    }
    switchMode("motion");
  }
}
