/*
global
action: false
L: false
page: false
visualization: false
*/

import { showRunServicePanel } from "./automation.js";
import {
  call,
  configureNamespace,
  history,
  historyPosition,
  moveHistory,
  notify,
  openPanel,
  serializeForm,
  showInstancePanel,
} from "./base.js";
import {
  showConnectionPanel,
  showDeviceData,
  showDeviceResultsPanel,
} from "./inventory.js";
import { tables } from "./table.js";

let selectedObject;
let markersArray = [];
let polylinesObjects = {};
let layer;
let markerType;
let map;
let markerGroup;
let clustered;
let devicesProperties = {};
let linksProperties = {};
let routerIcon;

let currentPath = localStorage.getItem(page);
let controls;

function updateRightClickBindings(controls) {
  Object.assign(action, {
    "Edit Pool": () => showInstancePanel("pool", currentPath),
    "Open Street Map": () => switchLayer("osm"),
    "Google Maps": () => switchLayer("gm"),
    Image: () => changeMarker("Image"),
    Circle: () => changeMarker("Circle"),
    "Circle Marker": () => changeMarker("Circle Marker"),
    Normal: () => displayNetwork({}),
    Clustered: () => displayNetwork({ withCluster: true }),
    Backward: () => displayNetwork({ direction: "left" }),
    Forward: () => displayNetwork({ direction: "right" }),
  });
}

function initLeaflet() {
  const settings = visualization.geographical;
  markerType = settings.marker;
  markerGroup = L.markerClusterGroup();
  map = L.map("map", { preferCanvas: true }).setView(
    [settings.latitude, settings.longitude],
    settings.zoom_level
  );
  layer = L.tileLayer(settings.layers[settings.tile_layer]);
  map
    .addLayer(layer)
    .on("click", function(e) {
      selectedObject = null;
    })
    .on("contextmenu", function() {
      if (!selectedObject) {
        $(".menu").hide();
        $(".geo-menu").show();
      }
    });
  for (const [key, value] of Object.entries(settings.icons)) {
    window[`icon_${key}`] = L.icon({
      iconUrl: `../static/img/network/default/${key}.gif`,
      iconSize: value,
      iconAnchor: [9, 6],
      popupAnchor: [8, -5],
    });
  }
  routerIcon = window["icon_router"];
}

function switchLayer(layerType) {
  map.removeLayer(layer);
  layer = L.tileLayer(visualization.geographical.layers[layerType]);
  map.addLayer(layer);
}

function changeMarker(type) {
  markerType = type;
  displayNetwork({});
}

function createNode(node) {
  if (!node.latitude && !node.longitude) return;
  devicesProperties[node.id] = node;
  let marker;
  try {
    marker =
      markerType == "Circle Marker"
        ? L.circleMarker([node.latitude, node.longitude])
        : markerType == "Circle"
        ? L.circle([node.latitude, node.longitude])
        : L.marker([node.latitude, node.longitude]);
  } catch (err) {
    return console.error(`Device '${node.name}' couldn't be loaded (${err})`);
  }
  if (markerType == "Image") {
    marker.icon =
      node.type === "device"
        ? (marker.icon = window[`icon_${node.icon}`] || routerIcon)
        : (marker.icon = window["icon_network"]);
    marker.setIcon(marker.icon);
  }
  marker.bindTooltip(node["name"], { permanent: false });
  marker.node_id = node.id;
  markersArray.push(marker);
  marker.on("click", function(e) {
    leftClickBinding("device", node.id, node.type == "site");
  });
  marker.on("contextmenu", function(e) {
    $(".menu").hide();
    $(`.rc-${node.type}-menu`).show();
    selectedObject = node;
  });
  if (clustered) {
    markerGroup.addLayer(marker);
  } else {
    marker.addTo(map);
  }
}

function createLink(link) {
  if (clustered || !link.destination_id || !link.source_id) return;
  linksProperties[link.id] = link;
  let pointA = new L.LatLng(link.source_latitude, link.source_longitude);
  let pointB = new L.LatLng(link.destination_latitude, link.destination_longitude);
  const pointList = [pointA, pointB];
  const polyline = new L.Polyline(pointList, {
    color: link.color,
    weight: 3,
    opacity: 1,
    smoothFactor: 1,
  });
  polylinesObjects[link.id] = polyline;
  polyline.link_id = link.id;
  polyline.on("click", function(e) {
    leftClickBinding("link", this.link_id, link.type == "bundle");
  });
  polyline.on("contextmenu", () => linkRightClickBinding(link));
  polyline.bindTooltip(link.name, {
    permanent: false,
  });
  polyline.addTo(map);
}

function linkRightClickBinding(link) {
  $(".menu").hide();
  if (link.type != "bundle") {
    $(".rc-link-menu").show();
    selectedObject = link;
  }
}

function deleteAllDevices() {
  for (let i = 0; i < markersArray.length; i++) {
    if (clustered) {
      markerGroup.removeLayer(markersArray[i]);
    } else {
      markersArray[i].removeFrom(map);
    }
  }
  markersArray = [];
}

function deleteAllLinks() {
  for (const polyline of Object.values(polylinesObjects)) {
    polyline.removeFrom(map);
  }
  polylinesObjects = {};
  linksProperties = {};
}

function deleteAll() {
  deleteAllDevices();
  deleteAllLinks();
}

function processNetwork(network) {
  let devices = {};
  for (const device of network.devices) {
    const key = `${device.longitude}/${device.latitude}`;
    devices[key] = devices[key] ? [...devices[key], device.id] : [device.id];
  }
  let colocatedDevices = new Set();
  for (const [coords, ids] of Object.entries(devices)) {
    if (ids.length == 1) continue;
    ids.forEach(colocatedDevices.add, colocatedDevices);
    const [longitude, latitude] = coords.split("/");
    network.devices.push({
      type: "site",
      name: `Site (${latitude},${longitude})`,
      icon: "network",
      id: ids.join("-"),
      longitude: longitude,
      latitude: latitude,
    });
  }
  network.devices = network.devices.filter(
    (device) => !colocatedDevices.has(device.id)
  );
  let links = {};
  let bundleCoordinates = {};
  for (const link of network.links) {
    const key = [
      `${link.source_latitude}/${link.source_longitude}`,
      `${link.destination_latitude}/${link.destination_longitude}`,
    ]
      .sort()
      .join("/");
    links[key] = links[key] ? [...links[key], link.id] : [link.id];
    if (!bundleCoordinates[key]) {
      bundleCoordinates[key] = {
        source_latitude: link.source_latitude,
        source_longitude: link.source_longitude,
        destination_latitude: link.destination_latitude,
        destination_longitude: link.destination_longitude,
      };
    }
  }
  let parallelLinks = new Set();
  for (const [endpoints, ids] of Object.entries(links)) {
    if (ids.length == 1) continue;
    ids.forEach(parallelLinks.add, parallelLinks);
    const [sourceId, destinationId] = endpoints.split("/");
    network.links.push({
      type: "bundle",
      name: "Colocated links",
      id: ids.join("-"),
      color: "#FF1493",
      source_id: parseInt(sourceId),
      destination_id: parseInt(destinationId),
      ...bundleCoordinates[endpoints],
    });
  }
  network.links = network.links.filter((link) => !parallelLinks.has(link.id));
}

function displayNetwork({ direction, noAlert, withCluster } = {}) {
  if (page == "view_builder") return;
  let data = {};
  currentPath =
    direction == "left"
      ? history[historyPosition - 1]
      : direction == "right"
      ? history[historyPosition + 1]
      : $("#current-pool").val();
  localStorage.setItem(page, currentPath);
  if (
    (direction == "left" && historyPosition == 0) ||
    (direction == "right" && historyPosition + 1 == history.length)
  ) {
    return;
  }
  moveHistory(currentPath, direction);
  $("#current-pool")
    .val(currentPath)
    .selectpicker("refresh");
  for (let type of ["device", "link"]) {
    let form = serializeForm(`#filtering-form-${type}`, `${type}_filtering`);
    if (currentPath) form.intersect = { type: "pool", id: currentPath };
    data[type] = { form: form };
  }
  deleteAll();
  clustered = withCluster;
  call({
    url: "/view_filtering",
    data: data,
    callback: function(network) {
      processNetwork(network);
      network.devices.map(createNode);
      network.links.map(createLink);
      map[clustered ? "addLayer" : "removeLayer"](markerGroup);
      if (!noAlert) notify("Filter applied.", "success", 5);
    },
  });
}

function leftClickBinding(type, id, bundle) {
  if (bundle) {
    const constraints = { id: `^(${id.split("-").join("|")})$`, id_filter: "regex" };
    showFilteredTable(id, type, constraints);
  } else {
    showInstancePanel(type, id);
  }
}

function showFilteredTable(id, type, constraints) {
  openPanel({
    name: "table",
    size: "1000 500",
    content: `
      <div class="modal-body">
        <div id="tooltip-overlay" class="overlay"></div>
        <form
          id="search-form-${type}-${id}"
          class="form-horizontal form-label-left"
          method="post"
        >
          <table
            id="table-${type}-${id}"
            class="table table-striped table-bordered table-hover"
            cellspacing="0"
            width="100%"
          ></table>
        </form>
      </div>`,
    id: id,
    title: `Colocated ${type}s`,
    tableId: `${type}-${id}`,
    callback: function() {
      // eslint-disable-next-line new-cap
      new tables[type](id, constraints);
    },
  });
}

function initFiltering() {
  for (let type of ["device", "link"]) {
    openPanel({
      name: `${type}_filtering`,
      type: type,
      title: `${type.charAt(0).toUpperCase() + type.slice(1)} Filtering`,
      size: "700 600",
      onbeforeclose: function() {
        $(this).css("visibility", "hidden");
      },
      css: { visibility: "hidden" },
    });
  }
}

export function initVisualization() {
  $("body").contextMenu({
    menuSelector: "#contextMenu",
    menuSelected: function(selectedMenu) {
      const row = selectedMenu.text();
      action[row](selectedObject);
      selectedObject = null;
    },
  });
  Object.assign(action, {
    Properties: (o) => showInstancePanel(o.type, o.id),
    Connect: (d) => showConnectionPanel(d),
    Configuration: (d) => showDeviceData(d),
    Results: (d) => showDeviceResultsPanel(d),
    "Run Service": (d) => showRunServicePanel({ instance: d }),
  });
  call({
    url: `/get_visualization_pools/${page}`,
    callback: function(pools) {
      pools.sort((a, b) => a.name.localeCompare(b.name));
      for (let i = 0; i < pools.length; i++) {
        $("#current-pool").append(
          `<option value="${pools[i].id}">${pools[i].name}</option>`
        );
      }
      if (currentPath && pools.some((w) => w.id == currentPath)) {
        $("#current-pool").val(currentPath);
        displayNetwork({ noAlert: true });
      } else {
        if ($("#current-pool").val()) {
          displayNetwork({ noAlert: true });
        } else {
          notify("No pool has been created yet.", "error", 5);
        }
      }
      $("#current-pool")
        .on("change", function() {
          displayNetwork();
        })
        .selectpicker({
          liveSearch: true,
        });
      updateRightClickBindings(controls);
    },
  });
  initFiltering();
  initLeaflet();
}

function displayFilteringPanel(type) {
  $(`#${type}_filtering`).css("visibility", "visible");
}

function clearSearch() {
  for (const table of ["device", "link"]) {
    $(`.search-input-${table},.search-list-${table}`).val("");
    $(".search-relation-dd")
      .val("any")
      .selectpicker("refresh");
    $(".search-relation")
      .val([])
      .trigger("change");
    $(`.search-select-${table}`)
      .val("inclusion")
      .selectpicker("refresh");
  }
  displayNetwork({ noAlert: true });
  notify("Search parameters cleared.", "success", 5);
}

configureNamespace("visualization", [
  clearSearch,
  displayFilteringPanel,
  displayNetwork,
]);
