/*
global
action: true
page: false
settings: false
*/

import { showRunServicePanel } from "./automation.js";
import {
  call,
  cantorPairing,
  configureNamespace,
  moveHistory,
  notify,
  openPanel,
  showInstancePanel,
  userIsActive,
} from "./base.js";
import {
  configureGraph,
  creationMode,
  currentMode,
  currentPath,
  edges,
  instance,
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
  if (site.nodes.length > visualization["Site Builder"].max_allowed_nodes) {
    return notify("The site contains too many nodes to be displayed.", "error", 5);
  }
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
    const node = nodes.get(this.getNodeAt(event.pointer.DOM));
    const linkId = this.getEdgeAt(event.pointer.DOM);
    if ((!node || !node.id) && !linkId) {
      return;
    } else if (node.type == "label") {
      showLabelPanel({ label: node, usePosition: true });
    } else if (node.type == "site") {
      switchToSite(`${currentPath}>${node.id}`);
    } else if (node && node.id) {
      showInstancePanel(node.type, node.id);
    } else if (linkId) {
      const link = edges.get(linkId);
      showInstancePanel(link.type, link.id);
    }
  });
}

export function drawSiteNode(node) {
  return {
    id: node.id,
    icon: node.icon,
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
    image: `/static/img/view/2D/default/${node.icon}.gif`,
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
  if (nodes.get(edge.from).type == "site" || nodes.get(edge.to).type == "site") {
    return notify("Cannot draw a link from or to a site", "error", 5);
  }
  showInstancePanel($("#edge-type-list").val(), null, null, null, edge);
}

export function showLinkPanel(type, id, edge) {
  $(id ? `#${type}-type-${id}` : `#${type}-type`)
    .val(type)
    .prop("disabled", true);
  $(id ? `#${type}-sites-${id}` : `#${type}-sites`).prop("disabled", true);
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

export function showNodePanel(type, id, mode) {
  $(id ? `#${type}-type-${id}` : `#${type}-type`)
    .val(type)
    .prop("disabled", true);
  if (id && mode == "duplicate" && type == "site") $(`#copy-${id}`).val(id);
  $(id ? `#${type}-sites-${id}` : `#${type}-sites`).prop("disabled", true);
}

function drawNetwork() {
  const enabled = graph.physics.physicsEnabled;
  graph.setOptions({
    physics: {
      enabled: !enabled,
      barnesHut: {
        gravitationalConstant: -100000,
        centralGravity: 0.5,
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
      document.body.style.cursor = "progress";
      result.nodes.map((node) => nodes.update(drawSiteNode(node)));
      result.links.map((link) => edges.update(drawSiteEdge(link)));
      $("#add_to_site").remove();
      notify("Objects added to the site.", "success", 5);
      document.body.style.cursor = "default";
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
    "Run Service": () =>
      showRunServicePanel({ type: "device", targets: graph.getSelectedNodes() }),
    "3D Visualization": (node) => showDeviceModel(node),
    "Edit Edge": (edge) => showInstancePanel(edge.type, edge.id),
  });
}

function displaySiteState(results) {
  nodes.update(
    Object.entries(results).map(([nodeId, success]) => {
      const color = success ? "green" : "red";
      const icon = nodes.get(parseInt(nodeId)).icon;
      const image = `/static/img/view/2D/${color}/${icon}.gif`;
      return { id: parseInt(nodeId), image: image };
    })
  );
}

export function getSiteState(periodic, first) {
  if (userIsActive && site?.id && !first) {
    call({
      url: `/get_site_state/${currentPath}`,
      data: { runtime: site.runtime },
      callback: function (result) {
        if (result.site.last_modified > instance.last_modified) {
          instance.last_modified = result.site.last_modified;
          displaySite(result.site);
        }
        if (result.device_results) displaySiteState(result.device_results);
      },
    });
  }
  if (periodic) setTimeout(() => getSiteState(true, false), 4000);
}

export function drawSiteEdge(link) {
  const key = cantorPairing(link.source_id, link.destination_id);
  const flip = link.source_id > link.destination_id;
  parallelLinks[key] = (parallelLinks[key] || 0) + 1;
  return {
    id: link.id,
    label: link.name,
    type: link.type,
    from: flip ? link.source_id : link.destination_id,
    to: flip ? link.destination_id : link.source_id,
    color: { color: link.color || "#000000" },
    smooth: {
      type: "curvedCCW",
      roundness: (parallelLinks[key] * (flip ? -1 : 1)) / 10,
    },
  };
}

configureNamespace("siteBuilder", [addObjectsToSite, filterSiteTable]);
