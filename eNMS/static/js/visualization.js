/*
global
action: false
Cesium: false
defaultPools: false
ForceGraph3D: false
jsPanel: false
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
  createTooltip,
  notify,
  serializeForm,
  showInstancePanel,
  openPanel,
} from "./base.js";
import { showConnectionPanel, showDeviceData } from "./inventory.js";
import { tables } from "./table.js";
import { currentRuntime } from "./workflow.js";

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

let currentMode = "map";
let currentPath = localStorage.getItem("view");
let currentView;
let camera;
let scene;
let renderer;
let controls;
let transformControls;
let labelRenderer;
let objects = [];
let pointer;
let raycaster;

function displayView(currentPath) {
  const [viewId] = currentPath.split(">").slice(-1);
  call({
    url: `/get/view/${viewId}`,
    callback: function (view) {
      currentView = view;
      camera = new THREE.PerspectiveCamera(
        45,
        $(".main_frame").width() / $(".main_frame").height(),
        1,
        10000
      );
      raycaster = new THREE.Raycaster();
      pointer = new THREE.Vector2();
      camera.position.set(500, 800, 1300);
      camera.lookAt(0, 0, 0);
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0xffffff);

      const helper = new THREE.GridHelper(2000, 100);
      helper.material.opacity = 0.5;
      helper.material.transparent = true;
      scene.add(helper);

      labelRenderer = new CSS2DRenderer();
      labelRenderer.setSize($(".main_frame").width(), $(".main_frame").height());
      labelRenderer.domElement.style.position = "absolute";
      const container = document.getElementById("map");
      renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.setSize($(".main_frame").width(), $(".main_frame").height());
      container.appendChild(labelRenderer.domElement);
      container.appendChild(renderer.domElement);
      controls = new THREE.OrbitControls(camera, labelRenderer.domElement);
      controls.addEventListener("change", render);
      controls.maxPolarAngle = Math.PI / 2;
      document.addEventListener("mousedown", onMouseDown, false);
      document.addEventListener("mousemove", onMouseMove, false);
      window.addEventListener("resize", onWindowResize, false);
      transformControls = new TransformControls(camera, labelRenderer.domElement);
      transformControls.addEventListener("change", render);
      transformControls.addEventListener("dragging-changed", function (event) {
        controls.enabled = !event.value;
      });
      scene.add(transformControls);
      updateRightClickBindings(controls);
      view.devices.map(drawNode);
      render();
    },
  });
}

function switchMode() {}

function drawNode(device) {
  const node = new THREE.Mesh(
    new THREE.CylinderGeometry(30, 30, 20, 32),
    new THREE.MeshBasicMaterial({
      color: 0x3c8c8c,
      opacity: 0.8,
      transparent: true,
    })
  );
  node.position.set(device.id * 100, device.id * 100, device.id * 100);
  drawLabel({ target: node, label: device.name });
  objects.push(node);
  scene.add(node);
  transformControls.attach(node);
}

function onMouseDown(event) {
  pointer.set(
    ((event.clientX - 250) / $(".main_frame").width()) * 2 - 1,
    -((event.clientY - 70) / $(".main_frame").height()) * 2 + 1
  );
  raycaster.setFromCamera(pointer, camera);
  const intersects = raycaster.intersectObjects(objects);
  
  if (intersects.length > 0) {
    
    const object = intersects[0].object;
    if (object !== transformControls.object) {
      transformControls.attach(object);
    }
  }
  if (!intersects.length) {
    $(".rc-object-menu").hide();
    $(".global").show();
  }
}

function onMouseMove(event) {
  pointer.set(
    ((event.clientX - 250) / $(".main_frame").width()) * 2 - 1,
    -((event.clientY - 70) / $(".main_frame").height()) * 2 + 1
  );
  raycaster.setFromCamera(pointer, camera);
  const intersects = raycaster.intersectObjects(objects);
  document.body.style.cursor = intersects.length > 0 ? "pointer" : "default";
}

function drawLabel({
  label,
  target = scene,
  style = { marginTop: "-1em", color: "#FF0000" },
} = {}) {
  const div = document.createElement("div");
  div.className = "label";
  div.textContent = label;
  Object.assign(div.style, style);
  const labelObject = new CSS2DObject(div);
  div.onclick = function () {
    console.log("test");
  };
  labelObject.position.set(0, 0, 0);
  target.add(labelObject);
}

function initLogicalFramework() {
  call({
    url: "/get_all/view",
    callback: function (views) {
      views.sort((a, b) => a.name.localeCompare(b.name));
      for (let i = 0; i < views.length; i++) {
        $("#current-view").append(
          `<option value="${views[i].id}">${views[i].name}</option>`
        );
      }
      if (currentPath && views.some((w) => w.id == currentPath.split(">")[0])) {
        $("#current-view").val(currentPath.split(">")[0]);
        displayView(currentPath);
      } else {
        currentPath = $("#current-view").val();
        if (currentPath) {
          displayView(currentPath);
        } else {
          notify("No view has been created yet.", "error", 5);
        }
      }
      $("#current-view").selectpicker({
        liveSearch: true,
      });
      updateRightClickBindings(controls);
    },
  });
}

function createNewView(mode) {
  if (mode == "create") {
    showInstancePanel("view");
  } else if (!currentView) {
    notify("No view has been created yet.", "error", 5);
  } else if (mode == "duplicate") {
    showInstancePanel("view", currentView.id, "duplicate");
  } else {
    showInstancePanel("view", currentView.id);
  }
}

function createLabel() {
  call({
    url: `/create_view_label/${currentView.id}`,
    form: "view_label-form",
    callback: function () {
      $("#view_label").remove();
      const div = document.createElement("div");
      div.className = "label";
      div.textContent = "Moon";
      div.style.marginTop = "-1em";
      const label = new CSS2DObject(div);
      label.position.set(0, 0, 0);
      notify("Label created.", "success", 5);
    },
  });
}

function addObjectPanel() {
  openPanel({
    name: "add_objects_to_view",
    title: "Add Objects to View",
    size: "800 350",
    callback: function () {},
  });
}

function addObjectsToView() {
  call({
    url: `/add_objects_to_view/${currentView.id}`,
    form: "add_objects_to_view-form",
    callback: function (result) {
      currentView.last_modified = result.update_time;
      $("#add_objects_to_view").remove();
      result.devices.map(drawNode);
      notify("Objects successfully added to the view.", "success", 5);
    },
  });
}

function updateRightClickBindings(controls) {
  Object.assign(action, {
    "Add to View": addObjectPanel,
    "Create View": () => createNewView("create"),
    "Create Label": () => openPanel({ name: "view_label", title: "Create New Label" }),
    "Edit View": () => createNewView("edit"),
    "Duplicate View": () => createNewView("duplicate"),
    "Zoom In": () => controls?.dollyOut(),
    "Zoom Out": () => controls?.dollyIn(),
  });
}

function render() {
  renderer.render(scene, camera);
  //labelRenderer.render(scene, camera);
}

function onWindowResize() {
  camera.aspect = $(".main_frame").width() / $(".main_frame").height();
  camera.updateProjectionMatrix();
  labelRenderer.setSize($(".main_frame").width(), $(".main_frame").height());
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

function init3dGeographicalFramework() {
  polylines = new Cesium.PolylineCollection();
  let providerViewModels = Object.entries(visualization.geographical._3D.layers).map(
    function ([name, properties]) {
      const iconUrl = `Widgets/Images/ImageryProviders/${properties.icon}.png`;
      return new Cesium.ProviderViewModel({
        category: properties.category,
        creationFunction: () =>
          new Cesium[properties.type](
            properties.type == "TileMapServiceImageryProvider"
              ? { url: Cesium.buildModuleUrl(properties.args.url) }
              : properties.type == "createWorldImagery"
              ? { style: Cesium.IonWorldImageryStyle[properties.arg] }
              : properties.args
          ),
        name: name,
        iconUrl: Cesium.buildModuleUrl(iconUrl),
        tooltip: properties.tooltip,
      });
    }
  );
  viewer = new Cesium.Viewer("map", {
    timeline: false,
    geocoder: false,
    animation: false,
    selectionIndicator: false,
    imageryProviderViewModels: providerViewModels,
  });
  viewer.scene.primitives.add(polylines);
  viewer.scene.postProcessStages.fxaa.enabled = true;
  $(".cesium-baseLayerPicker-dropDown > div").slice(2, 4).hide();
  labels = viewer.scene.primitives.add(new Cesium.LabelCollection());
  handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
  handler.setInputAction(onClick3d, Cesium.ScreenSpaceEventType.LEFT_CLICK);
  handler.setInputAction(onRightClick3d, Cesium.ScreenSpaceEventType.RIGHT_CLICK);
  handler.setInputAction(changeCursor, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
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

function createNode3d(node) {
  const icon = node.type === "device" ? node.icon || "router" : "site";
  let entity = {
    properties: node,
    position: Cesium.Cartesian3.fromDegrees(node.longitude, node.latitude),
    billboard: {
      image: `../static/img/view/3D/${icon}.gif`,
      scaleByDistance: new Cesium.NearFarScalar(1.5e2, 2.0, 1.5e7, 0.5),
    },
  };
  if (visualization.geographical._3D.labels.node) {
    entity.label = {
      fillColor: Cesium.Color.BLACK,
      text: node.name,
      scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.5, 8.0e6, 0.0),
      pixelOffset: new Cesium.Cartesian2(0.0, 20.0),
      font: "20px sans-serif",
    };
  }
  markersArray.push(viewer.entities.add(entity));
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
  linksProperties[link.id] = link;
  (dimension == "2D" ? createLink2d : createLink3d)(link);
}

function createLink3d(link) {
  const color = Cesium.Color.fromCssColorString(link.color.trim()) || "#000000";
  polylinesObjects[link.id] = polylines.add({
    id: link.id,
    positions: Cesium.Cartesian3.fromDegreesArray([
      link.source_longitude,
      link.source_latitude,
      link.destination_longitude,
      link.destination_latitude,
    ]),
    material: Cesium.Material.fromType("Color", {
      color: color,
    }),
    width: 1,
  });
  if (visualization.geographical._3D.labels.link) {
    labels.add({
      // eslint-disable-next-line new-cap
      position: new Cesium.Cartesian3.fromDegrees(...computeLinkMiddle(link), 0.0),
      scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.5, 8.0e6, 0.0),
      fillColor: Cesium.Color.BLACK,
      text: link.name,
    });
  }
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
    if (dimension == "3D") {
      viewer.entities.remove(markersArray[i]);
    } else if (clustered) {
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

Object.assign(action, {
  "Open Street Map": () => switchLayer("osm"),
  "Google Maps": () => switchLayer("gm"),
  Image: () => changeMarker("Image"),
  Circle: () => changeMarker("Circle"),
  "Circle Marker": () => changeMarker("Circle Marker"),
  Normal: () => displayNetwork({}),
  Clustered: () => displayNetwork({ withCluster: true }),
});

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
    const key = (page == "force_directed_view"
      ? [link.source_id, link.destination_id]
      : [
          `${link.source_latitude}/${link.source_longitude}`,
          `${link.destination_latitude}/${link.destination_longitude}`,
        ]
    )
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

function displayNetwork({ noAlert, withCluster }) {
  if (page == "logical_view") return;
  const maximumSize = visualization.logical.maximum_size;
  let data = {};
  for (let type of ["device", "link"]) {
    let form = serializeForm(`#search-form-${type}`);
    if (!form.pools) form.pools = defaultPools.map((p) => p.id);
    data[type] = { form: form };
  }
  clustered = withCluster;
  deleteAll();
  call({
    url: "/view_filtering",
    data: data,
    callback: function (network) {
      processNetwork(network);
      if (page == "force_directed_view") {
        if (
          network.devices.length > maximumSize.node ||
          network.links.length > maximumSize.link
        ) {
          return notify(
            `Too many objects to display. Use the device and link
            filtering mechanism to reduce the size of the network`,
            "error",
            5
          );
        }
        update3dGraphData(graph, network);
      } else {
        network.devices.map(createNode);
        network.links.map(createLink);
        if (dimension == "2D") {
          map[clustered ? "addLayer" : "removeLayer"](markerGroup);
        }
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
    const menu = isLink ? "link" : selectedObject.type == "pool" ? "site" : "device";
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
    const bundle = type == "site" || (typeof id === "string" && id.includes("-"));
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
      const sprite = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: new THREE.TextureLoader().load(`../static/img/view/2D/${icon}.gif`),
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

export function initView() {
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
    "Run Service": (d) => showRunServicePanel({ instance: d }),
  });
  for (let type of ["device", "link"]) {
    createTooltip({
      autoshow: true,
      persistent: true,
      name: `${type}_filtering`,
      target: `#${type}-filtering`,
      container: `#search-form-${type}`,
      size: "700 400",
      position: {
        my: "center-top",
        at: "center-bottom",
        offsetY: 10,
      },
      url: `../form/${type}_filtering`,
      title: `${type.charAt(0).toUpperCase() + type.slice(1)} Filtering`,
    });
  }
  if (page == "force_directed_view") {
    create3dGraphNetwork("network");
    notify("Loading network...", "success", 5);
  } else if (page == "geographical_view") {
    initGeographicalFramework();
  } else {
    initLogicalFramework();
  }
  displayNetwork({ noAlert: true });
}

function update3dGraphData(graph, network) {
  const nodesId = network.devices.map((node) => node.id);
  graph
    .graphData({
      nodes: network.devices,
      links: network.links
        .filter(
          (link) =>
            nodesId.includes(link.source_id) && nodesId.includes(link.destination_id)
        )
        .map((link) => {
          return {
            source: link.source_id,
            target: link.destination_id,
            value: 5,
            ...link,
          };
        }),
    })
    .refresh();
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

function saveParameters() {
  call({
    url: "/save_visualization_parameters",
    form: "visualization_parameters-form",
    callback: () => {
      notify("Default pools saved.", "success", 5);
      $("#visualization_parameters").remove();
    },
  });
}

function openVisualizationPanel() {
  openPanel({
    title: "Visualization Parameters",
    name: "visualization_parameters",
    size: "400 200",
    callback: () => {
      call({
        url: "/get_visualization_parameters",
        callback: (pools) => {
          const fieldId = "#visualization_parameters-default_pools";
          pools.forEach((pool) => {
            $(fieldId).append(new Option(pool.name, pool.id, false, false));
          });
          $(fieldId)
            .val(pools.map((pool) => pool.id))
            .trigger("change");
        },
      });
    },
  });
}

configureNamespace("visualization", [
  addObjectsToView,
  clearSearch,
  createLabel,
  displayNetwork,
  openVisualizationPanel,
  saveParameters,
  switchMode,
]);
