/*
global
action: false
Cesium: false
ForceGraph3D: false
L: false
page: false
SpriteText: false
theme: false
THREE: false
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

let graph;
let dimension;
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
let viewer;
let handler;
let polylines;
let labels;

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

function initGeographicalFramework() {
  dimension = visualization.geographical.default;
  if (dimension == "2D") {
    init2dGeographicalFramework();
  } else {
    init3dGeographicalFramework();
  }
}

function init2dGeographicalFramework() {
  const settings2d = visualization.geographical._2D;
  markerType = settings2d.marker;
  markerGroup = L.markerClusterGroup();
  map = L.map("map", { preferCanvas: true }).setView(
    [settings2d.latitude, settings2d.longitude],
    settings2d.zoom_level
  );
  layer = L.tileLayer(settings2d.layers[settings2d.tile_layer]);
  map
    .addLayer(layer)
    .on("click", function (e) {
      selectedObject = null;
    })
    .on("contextmenu", function () {
      if (!selectedObject) {
        $(".menu").hide();
        $(".geo-menu").show();
      }
    });
  for (const [key, value] of Object.entries(settings2d.icons)) {
    window[`icon_${key}`] = L.icon({
      iconUrl: `../static/img/view/3D/${key}.gif`,
      iconSize: value,
      iconAnchor: [9, 6],
      popupAnchor: [8, -5],
    });
  }
  routerIcon = window["icon_router"];
}

function switchLayer(layerType) {
  map.removeLayer(layer);
  layer = L.tileLayer(visualization.geographical._2D.layers[layerType]);
  map.addLayer(layer);
}

function changeMarker(type) {
  markerType = type;
  displayNetwork({});
}

function createNode(node) {
  if (!node.latitude && !node.longitude) return;
  devicesProperties[node.id] = node;
  (dimension == "2D" ? createNode2d : createNode3d)(node);
}

function createNode2d(node) {
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
        : (marker.icon = window["icon_site"]);
    marker.setIcon(marker.icon);
  }
  marker.bindTooltip(node["name"], { permanent: false });
  marker.node_id = node.id;
  markersArray.push(marker);
  marker.on("click", function (e) {
    leftClickBinding("device", node.id, node.type == "site");
  });
  marker.on("contextmenu", function (e) {
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
  if (!link.destination_id || !link.source_id) return;
  linksProperties[link.id] = link;
  (dimension == "2D" ? createLink2d : createLink3d)(link);
}

function computeLinkMiddle(link) {
  const [φ1, φ2, λ1, λ2] = [
    link.source_latitude,
    link.destination_latitude,
    link.source_longitude,
    link.destination_longitude,
  ].map((coordinate) => (coordinate * Math.PI) / 180);
  const Bx = Math.cos(φ2) * Math.cos(λ2 - λ1);
  const By = Math.cos(φ2) * Math.sin(λ2 - λ1);
  const φ3 = Math.atan2(
    Math.sin(φ1) + Math.sin(φ2),
    Math.sqrt((Math.cos(φ1) + Bx) * (Math.cos(φ1) + Bx) + By * By)
  );
  const λ3 = λ1 + Math.atan2(By, Math.cos(φ1) + Bx);
  return [λ3 * (180 / Math.PI), φ3 * (180 / Math.PI)];
}

function createLink2d(link) {
  if (clustered) return;
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
  polyline.on("click", function (e) {
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
    if (dimension == "2D") {
      polyline.removeFrom(map);
    } else {
      polylines.remove(polyline);
    }
  }
  polylinesObjects = {};
  linksProperties = {};
}

function deleteAll() {
  deleteAllDevices();
  deleteAllLinks();
}

function processNetwork(network) {
  if (page == "geographical_view") {
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
        icon: "site",
        id: ids.join("-"),
        longitude: longitude,
        latitude: latitude,
      });
    }
    network.devices = network.devices.filter(
      (device) => !colocatedDevices.has(device.id)
    );
  }
  let links = {};
  let bundleCoordinates = {};
  for (const link of network.links) {
    const key = [
          `${link.source_latitude}/${link.source_longitude}`,
          `${link.destination_latitude}/${link.destination_longitude}`,
        ].sort().join("/");
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
  $("#current-pool").val(currentPath).selectpicker("refresh");
  for (let type of ["device", "link"]) {
    let form = serializeForm(`#filtering-form-${type}`, `${type}_filtering`);
    if (currentPath) form.intersect = { type: "pool", id: currentPath };
    data[type] = { form: form };
  }
  clustered = withCluster;
  deleteAll();
  call({
    url: "/view_filtering",
    data: data,
    callback: function (network) {
      processNetwork(network);
      network.devices.map(createNode);
      network.links.map(createLink);
      if (dimension == "2D") {
        map[clustered ? "addLayer" : "removeLayer"](markerGroup);
      }
      if (!noAlert) notify("Filter applied.", "success", 5);
    },
  });
}

function changeCursor(click) {
  const instance = viewer.scene.pick(click.endPosition);
  document.body.style.cursor = instance ? "pointer" : "default";
}

function onRightClick3d(click) {
  const instance = viewer.scene.pick(click.position);
  if (instance) {
    const isLink = typeof instance.id == "number";
    const id = isLink ? instance.id : instance.id._properties._id._value;
    selectedObject = (isLink ? linksProperties : devicesProperties)[id];
    const menu = isLink ? "link" : selectedObject.type == "pool" ? "network" : "device";
    $(".menu").hide();
    $(`.rc-${menu}-menu`).show();
  } else {
    selectedObject = null;
    $(".menu").hide();
  }
}

function leftClickBinding(type, id, bundle) {
  if (bundle) {
    const constraints = { id: `^(${id.split("-").join("|")})$`, id_filter: "regex" };
    showFilteredTable(id, type, constraints);
  } else {
    showInstancePanel(type, id);
  }
}

function onClick3d(click) {
  const instance = viewer.scene.pick(click.position);
  if (instance) {
    const isLink = ["number", "string"].includes(typeof instance.id);
    const id = isLink ? instance.id : instance.id._properties._id._value;
    const type = isLink ? "link" : instance.id._properties._type._value;
    const bundle = type == "network" || (typeof id === "string" && id.includes("-"));
    leftClickBinding(isLink ? "link" : "device", id, bundle);
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
    callback: function () {
      // eslint-disable-next-line new-cap
      new tables[type](id, constraints);
    },
  });
}

function create3dGraphNetwork(container) {
  const viewSettings = visualization.logical;
  const network = document.getElementById(container);
  // eslint-disable-next-line new-cap
  graph = ForceGraph3D(viewSettings.config)(network);
  graph
    .width($(".main_frame").width() + 20)
    .height($(".main_frame").height() - 90)
    .backgroundColor(theme.view.logical.background)
    .onBackgroundRightClick(() => {
      $(".menu").hide();
    })
    .onNodeHover((node) => (network.style.cursor = node ? "pointer" : null))
    .onNodeClick((node) => {
      const ratio = 1 + 100 / Math.hypot(node.x, node.y, node.z);
      const position = { x: node.x * ratio, y: node.y * ratio, z: node.z * ratio };
      graph.cameraPosition(position, node, 1500);
      setTimeout(() => showInstancePanel(node.type, node.id), 1550);
    })
    .onNodeRightClick((node) => {
      $(".menu").show();
      selectedObject = node;
    })
    .onLinkHover((link) => (network.style.cursor = link ? "pointer" : null))
    .onLinkClick((link) => leftClickBinding("link", link.id, link.type == "bundle"))
    .onLinkRightClick((link) => linkRightClickBinding(link))
    .linkWidth(viewSettings.link_width)
    .linkOpacity(viewSettings.link_opacity)
    .linkCurveRotation("rotation");
  if (viewSettings.display_link_label) {
    graph
      .linkThreeObjectExtend(true)
      .linkThreeObject((link) => {
        const sprite = new SpriteText(link.name);
        sprite.color = theme.view.logical.label;
        sprite.textHeight = 3;
        return sprite;
      })
      .linkPositionUpdate((sprite, { start, end }) => {
        Object.assign(
          sprite.position,
          Object.assign(
            ...["x", "y", "z"].map((c) => ({
              [c]: start[c] + (end[c] - start[c]) / 2,
            }))
          )
        );
      });
  }
  if (viewSettings.display_link_traffic) {
    graph
      .linkDirectionalParticles("value")
      .linkDirectionalParticleSpeed((d) => d.value * viewSettings.traffic_speed);
  }
  if (viewSettings.display_icons) {
    graph.nodeThreeObject(({ icon }) => {
      const image = new THREE.Mesh(
        new THREE.SphereGeometry(7),
        new THREE.MeshBasicMaterial({
          depthWrite: false,
          color: theme.view.logical.sphere,
        })
      );
      const imageUrl = `../static/img/view/2D/default/${icon}.gif`;
      const sprite = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: new THREE.TextureLoader().load(imageUrl),
          alphaTest: 0.5,
        })
      );
      sprite.scale.set(10, 10);
      image.add(sprite);
      return image;
    });
  }
  return graph;
}

function initFiltering() {
  for (let type of ["device", "link"]) {
    openPanel({
      name: `${type}_filtering`,
      type: type,
      title: `${type.charAt(0).toUpperCase() + type.slice(1)} Filtering`,
      size: "700 600",
      onbeforeclose: function () {
        $(this).css("visibility", "hidden");
      },
      css: { visibility: "hidden" },
    });
  }
}

export function showDeviceModel(device) {
  openPanel({
    name: "device_view",
    title: `3D Visualization of '${device.name}'`,
    size: "700 500",
    id: device.id,
    content: `<div id="3D-${device.id}" style="height:100%; width:100%"></div>`,
    callback: () => {
      const aspect = $(".main_frame").width() / $(".main_frame").height();
      let camera = new THREE.PerspectiveCamera(45, aspect, 1, 100000);
      camera.position.set(...visualization.icons["3D"][device.icon_3d].position);
      let scene = new THREE.Scene();
      scene.background = new THREE.Color(0xffffff);
      const container = document.getElementById(`3D-${device.id}`);
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(700, 485);
      container.appendChild(renderer.domElement);
      const ambientLight = new THREE.AmbientLight(0xcccccc, 0.4);
      scene.add(ambientLight);
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(1, 1, 0).normalize();
      scene.add(directionalLight);
      new THREE.OrbitControls(camera, renderer.domElement);
      new THREE.ColladaLoader().load(
        `/static/img/view/models/${device.icon_3d}.dae`,
        function (collada) {
          collada.scene.scale.set(20, 20, 20);
          collada.scene.rotation.set(-Math.PI / 2, 0, Math.PI / 2);
          collada.scene.position.set(2300, 0, 800);
          scene.add(collada.scene);
        }
      );
      (function render() {
        requestAnimationFrame(render);
        renderer.render(scene, camera);
      })();
    },
  });
}

export function initVisualization() {
  $("body").contextMenu({
    menuSelector: "#contextMenu",
    menuSelected: function (selectedMenu) {
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
    "3D Visualization": (d) => showDeviceModel(d),
  });
  call({
    url: `/get_visualization_pools/${page}`,
    callback: function (pools) {
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
        .on("change", function () {
          displayNetwork();
        })
        .selectpicker({
          liveSearch: true,
        });
      updateRightClickBindings(controls);
    },
  });
  initFiltering();
  initGeographicalFramework();
}

function displayFilteringPanel(type) {
  $(`#${type}_filtering`).css("visibility", "visible");
}

function clearSearch() {
  for (const table of ["device", "link"]) {
    $(`.search-input-${table},.search-list-${table}`).val("");
    $(".search-relation-dd").val("any").selectpicker("refresh");
    $(".search-relation").val([]).trigger("change");
    $(`.search-select-${table}`).val("inclusion").selectpicker("refresh");
  }
  displayNetwork({ noAlert: true });
  notify("Search parameters cleared.", "success", 5);
}

configureNamespace("visualization", [
  clearSearch,
  displayFilteringPanel,
  displayNetwork,
]);
