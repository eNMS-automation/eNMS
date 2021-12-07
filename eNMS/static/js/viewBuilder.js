/*
global
action: false
CSS2DObject: false
CSS2DRenderer: false
page: false
THREE: false
*/

import { showRunServicePanel } from "./automation.js";
import {
  call,
  history,
  historyPosition,
  moveHistory,
  notify,
  openPanel,
  showInstancePanel,
} from "./base.js";
import { showConnectionPanel, showDeviceData } from "./inventory.js";

let selectedObject;
let currentView;
let selectedObjects = [];
let camera;
let scene;
let renderer;
let controls;
let nodes = {};
let texture;
let daeModels = {};
let lineGeometries = [];

let currentPath = localStorage.getItem(page);

function displayView({ direction } = {}) {
  currentPath =
    direction == "left"
      ? history[historyPosition - 1]
      : direction == "right"
      ? history[historyPosition + 1]
      : $("#current-view").val();
  if (typeof currentPath === "undefined") return;
  const [viewId] = currentPath.split(">").slice(-1);
  localStorage.setItem(page, currentPath);
  moveHistory(currentPath, direction);
  $("#current-view").val(currentPath).selectpicker("refresh");
  call({
    url: `/get/view/${viewId}`,
    callback: function (view) {
      nodes = {};
      selectedObject = [];
      currentView = view;
      const aspect = $(".main_frame").width() / $(".main_frame").height();
      camera = new THREE.PerspectiveCamera(45, aspect, 1, 10000);
      camera.position.set(500, 800, 1300);
      camera.lookAt(0, 0, 0);
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0xffffff);
      const container = document.getElementById("map");
      $("#map").empty();
      renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.setSize($(".main_frame").width(), $(".main_frame").height());
      container.appendChild(renderer.domElement);
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.addEventListener("change", render);
      controls.maxPolarAngle = Math.PI / 2;
      window.addEventListener("resize", onWindowResize, false);
      const ambientLight = new THREE.AmbientLight(0xcccccc, 0.4);
      scene.add(ambientLight);
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(1, 1, 0).normalize();
      scene.add(directionalLight);
      updateRightClickBindings(controls);
      view.objects.map(drawNode);
      render();
    },
  });
}

function setNodePosition(node, properties) {
  node.scale.set(properties.scale_x, properties.scale_y, properties.scale_z);
  node.rotation.set(
    properties.rotation_x,
    properties.rotation_y,
    properties.rotation_z
  );
  node.position.set(
    properties.position_x,
    properties.position_y,
    properties.position_z
  );
}

function deleteSelection() {
  call({
    url: "/delete_view_selection",
    data: { selection: selectedObjects.map((mesh) => mesh.userData.id) },
    callback: function (updateTime) {
      selectedObjects.map(deleteMesh);
      selectedObjects = [];
      currentView.last_modified = updateTime;
      render();
      notify("Selection successfully deleted.", "success", 5);
    },
  });
}

function deleteMesh(mesh) {
  delete nodes[mesh.userData.id];
  scene.remove(mesh);
}

function savePositions() {
  call({
    url: "/save_view_positions",
    data: Object.fromEntries(
      Object.entries(nodes).map(([nodeId, node]) => [
        nodeId,
        { position: node.position, scale: node.scale, rotation: node.rotation },
      ])
    ),
    callback: function (updateTime) {
      if (updateTime) currentView.last_modified = updateTime;
    },
  });
}

function drawNode(node) {
  let geometry;
  let material;

  if (node.model) {
    new THREE.ColladaLoader().load(
      `/static/img/view/models/${node.model}.dae`,
      function (collada) {
        daeModels[node.id] = collada.scene;
        setNodePosition(daeModels[node.id], node);
        daeModels[node.id].traverse(function (child) {
          child.userData = { isCollada: true, ...node };
        });
        nodes[node.id] = daeModels[node.id];
        scene.add(daeModels[node.id]);
      }
    );
    return;
  }
  const mesh = new THREE.Mesh(geometry, material);
  nodes[node.id] = mesh;
  mesh.userData = node;
  scene.add(mesh);
}

function initLogicalFramework() {
  texture = new THREE.TextureLoader().load("/static/img/textures/floor3.jpg");
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
        displayView();
      } else {
        currentPath = $("#current-view").val();
        if (currentPath) {
          displayView();
        } else {
          notify("No view has been created yet.", "error", 5);
        }
      }
      $("#current-view")
        .on("change", function () {
          if (this.value != currentView.id) displayView();
        })
        .selectpicker({
          liveSearch: true,
        });
      updateRightClickBindings(controls);
    },
  });
  $("#transform-mode").selectpicker();
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

export function viewCreation(instance) {
  if (instance.type == "view") {
    if (instance.id == currentView.id) {
      $("#current-view option:selected").text(instance.name).trigger("change");
    } else {
      $("#current-view").append(
        `<option value="${instance.id}">${instance.name}</option>`
      );
      $("#current-view").val(instance.id).trigger("change");
      displayView();
    }
  } else if (instance.type == "node") {
    setNodePosition(nodes[instance.id], instance);
  }
}

function updateRightClickBindings(controls) {
  Object.assign(action, {
    "Add to View": () => showInstancePanel("node"),
    "Create View": () => createNewView("create"),
    "Create Label": () => openPanel({ name: "view_label", title: "Create New Label" }),
    "Edit View": () => createNewView("edit"),
    "Edit Pool": () => showInstancePanel("pool", currentPath),
    Delete: () => deleteSelection(),
    "Duplicate View": () => createNewView("duplicate"),
    "Zoom In": () => controls?.dollyOut(),
    "Zoom Out": () => controls?.dollyIn(),
    Backward: () => displayView({ direction: "left" }),
    Forward: () => displayView({ direction: "right" }),
  });
}

function render() {
  for (const geometry of lineGeometries) {
    geometry.verticesNeedUpdate = true;
  }
  if (renderer) renderer.render(scene, camera);
}

function onWindowResize() {
  camera.aspect = $(".main_frame").width() / $(".main_frame").height();
  camera.updateProjectionMatrix();
}

export function initViewBuilder() {
  $("body").contextMenu({
    menuSelector: "#contextMenu",
    menuSelected: function (selectedMenu) {
      const row = selectedMenu.text();
      action[row](selectedObject);
      selectedObject = null;
    },
  });
  Object.assign(action, {
    "View Properties": (viewObject) => showInstancePanel("node", viewObject.id),
    Connect: (viewObject) => showConnectionPanel(viewObject.device),
    Configuration: (viewObject) => showDeviceData(viewObject.device),
    "Run Service": (viewObject) => showRunServicePanel({ instance: viewObject.device }),
  });
  initLogicalFramework();
}

function animate() {
  requestAnimationFrame(animate);
  render();
}

animate();
