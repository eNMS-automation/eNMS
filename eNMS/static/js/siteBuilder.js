/*
global
page: false
*/

import { showRunServicePanel } from "./automation.js";
import {
  call,
  configureNamespace,
  moveHistory,
  notify,
  openPanel,
  showInstancePanel,
} from "./base.js";
import {
  configureGraph,
  creationMode,
  currentMode,
  currentPath,
  edges,
  nodes,
  setPath,
  savePositions,
  showLabelPanel,
  switchMode,
  updateBuilderBindings,
} from "./builder.js";
import {
  showConnectionPanel,
  showDeviceData,
  showDeviceResultsPanel,
} from "./inventory.js";
import { clearSearch, tableInstances } from "./table.js";
import { showDeviceModel } from "./visualization.js";

let graph;
let parallelLinks = {};
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
        switchMode(currentMode, true);
      } else {
        $("#site-filtering").val(path ? site.name : "");
        tableInstances["site"].table.page(0).ajax.reload(null, false);
      }
    },
  });
}

export function displaySite(site) {
  parallelLinks = {};
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
    icon_3d: node.icon_3d,
    color: "#D2E5FF",
    font: {
      size: 15,
      multi: "html",
      align: "center",
      bold: { color: "#000000" },
    },
    label: node.name,
    name: node.name,
    type: node.type,
    image: `/static/img/view/2D/${node.icon}.gif`,
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
  showInstancePanel($("#edge-type").val(), null, null, null, edge);
}

export function showLinkPanel(type, id, edge) {
  $(id ? `#${type}-type-${id}` : `#${type}-type`)
    .val(type)
    .prop("disabled", true);
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

function drawNetwork() {
  const enabled = graph.physics.physicsEnabled;
  graph.setOptions({
    physics: {
      enabled: !enabled,
      barnesHut: {
        springLength: 250,
        springConstant: 0.05,
        damping: 0.09,
      },
    },
  });
  const status = enabled ? "disabled" : "enabled";
  if (enabled) savePositions();
  notify(`Automatic Display ${status}.`, "success", 5);
}

function addObjectsToSite() {
  call({
    url: `/add_objects_to_site/${site.id}`,
    form: "add_to_site-form",
    callback: function (result) {
      result.nodes.map((node) => nodes.update(drawSiteNode(node)));
      result.links.map((link) => edges.update(drawSiteEdge(link)));
      $("#add_to_site").remove();
    },
  });
}

function openAddToSitePanel() {
  openPanel({
    name: "add_to_site",
    title: `Add objects to site '${site.name}'`,
    size: "800 350",
  });
}

export function updateSiteRightClickBindings() {
  updateBuilderBindings(action);
  Object.assign(action, {
    "Add to Site": openAddToSitePanel,
    "Automatic Layout": () => drawNetwork(),
    Connect: (node) => showConnectionPanel(node),
    Configuration: (node) => showDeviceData(node),
    Results: (node) => showDeviceResultsPanel(node),
    "Run Service": () => showRunServicePanel({ type: "device", targets: graph.getSelectedNodes() }),
    "3D Visualization": (node) => showDeviceModel(node),
    "Edit Edge": (edge) => showInstancePanel(edge.type, edge.id),
  });
}

function communtativePairing(a, b) {
  return (Math.max(a, b) * (Math.max(a, b) + 1)) / 2 + Math.min(a, b);
}

export function drawSiteEdge(link) {
  const key = communtativePairing(link.source_id, link.destination_id);
  parallelLinks[key] = (parallelLinks[key] || 0) + 1;
  const isEven = parallelLinks[key] % 2 === 0;
  return {
    id: link.id,
    label: link.name,
    type: link.type,
    from: link.source_id,
    to: link.destination_id,
    color: { color: link.color },
    smooth: {
      type: "curvedCW",
      forceDirection: "none",
      roundness: ((parallelLinks[key] - isEven) / 20) * (isEven ? -1 : 1),
    },
  };
}

configureNamespace("siteBuilder", [addObjectsToSite, filterSiteTable, showLinkPanel]);
