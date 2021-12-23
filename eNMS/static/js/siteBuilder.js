/*
global
page: false
*/

import { showRunServicePanel } from "./automation.js";
import {
  call,
  configureNamespace,
  history,
  historyPosition,
  moveHistory,
  showInstancePanel,
} from "./base.js";
import {
  configureGraph,
  createNewNode,
  creationMode,
  currentMode,
  currentPath,
  nodes,
  setPath,
  showLabelPanel,
  updateBuilderBindings,
} from "./builder.js";
import { showConnectionPanel, showDeviceData, showDeviceResultsPanel } from "./inventory.js";
import { clearSearch, tableInstances } from "./table.js";
import { showDeviceModel } from "./visualization.js";

let graph;
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
    addEdge: function (data, callback) {
      saveLink(data);
    },
    deleteNode: function (data, callback) {
      callback(data);
    },
  },
};

export function switchToSite(path, direction) {
  if (typeof path === "undefined") return;
  setPath(path.toString());
  if (currentPath.includes(">")) {
    $("#up-arrow").removeClass("disabled");
  } else {
    $("#up-arrow").addClass("disabled");
  }
  moveHistory(path, direction);
  if (!path && page == "site_table") {
    $("#site-filtering").val("");
    tableInstances["site"].table.page(0).ajax.reload(null, false);
    return;
  }
  const [siteId] = currentPath.split(">").slice(-1);
  call({
    url: `/get/site/${siteId}`,
    callback: function (newSite) {
      site = newSite;
      if (page == "site_builder") {
        localStorage.setItem("path", path);
        if (site) localStorage.setItem("site", JSON.stringify(site));
        displaySite(site);
      } else {
        $("#site-filtering").val(path ? site.name : "");
        tableInstances["site"].table.page(0).ajax.reload(null, false);
      }
    },
  });
}

export function displaySite(site) {
  graph = configureGraph(
    site,
    {
      nodes: site.nodes.map(drawSiteNode),
      edges: site.links.map(drawSiteEdge),
      inactive: new Set(),
    },
    options
  );
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

export function drawSiteNode(node) {
  return {
    id: node.id,
    color: "#D2E5FF",
    font: {
      size: 15,
      multi: "html",
      align: "center",
      bold: { color: "#000000" },
    },
    shadow: {
      enabled: !node.shared,
      color: "#6666FF",
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

export function updateSitePanel(type) {
  if (currentMode == "motion" && creationMode == "create_node") {
    $(`#${type}-sites`).append(new Option(site.name, site.name));
    $(`#${type}-sites`).val(site.name).trigger("change");
  }
}

function filterSiteTable(tableId, path) {
  clearSearch(tableId);
  switchToSite(path);
}

function saveLink(edge) {
  showInstancePanel($("#link-type").val(), null, null, null, edge);
}

export function showLinkPanel(type, id, edge) {
  $(id ? `#${type}-type-${id}` : `#${type}-type`)
    .val(type)
    .prop("disabled", true);
  $(id ? `#${type}-name-${id}` : `#${type}-name`).prop("disabled", true);
  if (edge) {
    const sourceName = nodes.get(edge.from).name;
    const destinationName = nodes.get(edge.to).name;
    $(`#${type}-sites`)
      .append(new Option(site.name, site.name))
      .val([site.name])
      .trigger("change");
    $(`#${type}-source`)
      .append(new Option(sourceName, edge.from))
      .val([edge.from])
      .trigger("change");
    $(`#${type}-destination`)
      .append(new Option(destinationName, edge.to))
      .val([edge.to])
      .trigger("change");
  }
}

export function updateSiteRightClickBindings() {
  updateBuilderBindings(action);
  Object.assign(action, {
    "Create Site": () => createNewNode("create_site"),
    "Duplicate Site": () => createNewNode("duplicate_site"),
    "Create New Node": () => createNewNode("create_node"),
    Connect: (node) => showConnectionPanel(node),
    Configuration: (node) => showDeviceData(node),
    Results: (node) => showDeviceResultsPanel(node),
    "Run Service": (node) => showRunServicePanel({ instance: node }),
    "3D Visualization": (node) => showDeviceModel(node.id),
    "Edit Site": () => showInstancePanel("site", site?.id),
    "Edit Edge": (edge) => showInstancePanel(edge.type, edge.id),
    "Enter Site": (node) => switchToSite(`${currentPath}>${node.id}`),
    "Site Backward": () => switchToSite(history[historyPosition - 1], "left"),
    "Site Forward": () => switchToSite(history[historyPosition + 1], "right"),
    "Site Upward": () => {
      const parentPath = currentPath.split(">").slice(0, -1).join(">");
      if (parentPath) switchToSite(parentPath);
    },
  });
}

export function drawSiteEdge(link) {
  return {
    id: link.id,
    label: link.scoped_name,
    type: link.type,
    from: link.source_id,
    to: link.destination_id,
    color: { color: link.color },
  };
}

configureNamespace("siteBuilder", [filterSiteTable, showLinkPanel]);
