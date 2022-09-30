/*
global
action: true
visualization: false
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
import { clearSearch } from "./table.js";

const displayImage = visualization["Network Builder"].display_nodes_as_images;

let graph;
let parallelLinks = {};
export let network = JSON.parse(localStorage.getItem("network"));

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

export function switchToNetwork(path, direction) {
  if (typeof path === "undefined") return;
  setPath(path.toString());
  if (currentPath.includes(">")) {
    $("#up-arrow").removeClass("disabled");
  } else {
    $("#up-arrow").addClass("disabled");
  }
  moveHistory(path, direction);
  $("#automatic-layout-btn").removeClass("active");
  const [networkId] = currentPath.split(">").slice(-1);
  call({
    url: `/get/network/${networkId}`,
    callback: function (newNetwork) {
      network = newNetwork;
      localStorage.setItem("network_path", path);
      if (network) localStorage.setItem("network", JSON.stringify(network));
      displayNetwork(network);
      switchMode(currentMode, true);
    },
  });
}

export function displayNetwork(network) {
  if (network.nodes.length > visualization["Network Builder"].max_allowed_nodes) {
    return notify("The network contains too many nodes to be displayed.", "error", 5);
  }
  parallelLinks = {};
  graph = configureGraph(
    network,
    {
      nodes: network.nodes.map(drawNetworkNode),
      edges: network.links.map(drawNetworkEdge),
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
    } else if (node.type == "network") {
      switchToNetwork(`${currentPath}>${node.id}`);
    } else if (node && node.id) {
      showInstancePanel(node.type, node.id);
    } else if (linkId) {
      const link = edges.get(linkId);
      showInstancePanel(link.type, link.id);
    }
  });
}

export function drawNetworkNode(node) {
  return {
    id: node.id,
    icon: node.icon,
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
    image: displayImage ? `/static/img/network/default/${node.icon}.gif` : undefined,
    shape: displayImage ? "image" : "ellipse",
    x: node.positions[network.name] ? node.positions[network.name][0] : 0,
    y: node.positions[network.name] ? node.positions[network.name][1] : 0,
  };
}

export function updateNetworkPanel(type) {
  if (currentMode == "motion" && creationMode == "create_node") {
    $(`#${type}-networks`).append(new Option(network.name, network.name));
    $(`#${type}-networks`).val(network.name).trigger("change");
  }
}

function filterNetworkTable(tableId, path) {
  clearSearch(tableId);
  switchToNetwork(path);
}

function saveLink(edge) {
  if (nodes.get(edge.from).type == "network" || nodes.get(edge.to).type == "network") {
    return notify("Cannot draw a link from or to a network", "error", 5);
  }
  showInstancePanel($("#edge-type-list").val(), null, null, null, edge);
}

export function showLinkPanel(type, id, edge) {
  $(id ? `#${type}-type-${id}` : `#${type}-type`)
    .val(type)
    .prop("disabled", true);
  $(id ? `#${type}-networks-${id}` : `#${type}-networks`).prop("disabled", true);
  if (edge) {
    const sourceName = nodes.get(edge.from).name;
    const destinationName = nodes.get(edge.to).name;
    $(`#${type}-networks`)
      .append(new Option(network.name, network.name))
      .val([network.name])
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
  if (id && mode == "duplicate" && type == "network") $(`#copy-${id}`).val(id);
  $(id ? `#${type}-networks-${id}` : `#${type}-networks`).prop("disabled", true);
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
  $("#automatic-layout-btn").toggleClass("active");
  const status = enabled ? "disabled" : "enabled";
  if (enabled) savePositions();
  notify(`Automatic Display ${status}.`, "success", 5);
}

function addObjectsToNetwork() {
  call({
    url: `/add_objects_to_network/${network.id}`,
    form: "add_to_network-form",
    callback: function (result) {
      document.body.style.cursor = "progress";
      result.nodes.map((node) => nodes.update(drawNetworkNode(node)));
      result.links.map((link) => edges.update(drawNetworkEdge(link)));
      document.body.style.cursor = "default";
      $("#add_to_network").remove();
      notify("Objects added to the network.", "success", 5);
    },
  });
}

function openAddToNetworkPanel() {
  openPanel({
    name: "add_to_network",
    title: `Add objects to network '${network.name}'`,
    size: "800 350",
  });
}

export function updateNetworkRightClickBindings() {
  updateBuilderBindings(action);
  Object.assign(action, {
    "Add to Network": openAddToNetworkPanel,
    "Automatic Layout": () => drawNetwork(),
    Connect: (node) => showConnectionPanel(node),
    Configuration: (node) => showDeviceData(node),
    Results: (node) => showDeviceResultsPanel(node),
    "Run Service": () => {
      if (!graph) return;
      showRunServicePanel({ type: "device", targets: graph.getSelectedNodes() });
    },
    "Edit Edge": (edge) => showInstancePanel(edge.type, edge.id),
  });
}

function displayNetworkState(results) {
  nodes.update(
    Object.entries(results).map(([nodeId, success]) => {
      const color = success ? "green" : "red";
      const icon = nodes.get(parseInt(nodeId)).icon;
      const image = `/static/img/network/${color}/${icon}.gif`;
      return { id: parseInt(nodeId), image: image };
    })
  );
}

export function getNetworkState(periodic, first) {
  if (userIsActive && network?.id && !first) {
    call({
      url: `/get_network_state/${currentPath}`,
      data: { runtime: network.runtime },
      callback: function (result) {
        if (result.network.last_modified > instance.last_modified) {
          instance.last_modified = result.network.last_modified;
          displayNetwork(result.network);
        }
        if (result.device_results) displayNetworkState(result.device_results);
      },
    });
  }
  if (periodic) setTimeout(() => getNetworkState(true, false), 4000);
}

export function drawNetworkEdge(link) {
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

export function resetNetworkDisplay() {
  let nodeUpdates = [];
  network.nodes.forEach((node) => {
    nodeUpdates.push({
      id: node.id,
      image: `/static/img/network/default/${node.icon}.gif`,
    });
  });
  if (nodes) nodes.update(nodeUpdates);
}

configureNamespace("networkBuilder", [addObjectsToNetwork, filterNetworkTable]);
