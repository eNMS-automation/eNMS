/*
global
action: false
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

let currentView;
let camera;
let scene;
let renderer;
let controls;
let nodes = {};
let daeModels = {};

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
      currentView = view;
      const aspect = $(".main_frame").width() / $(".main_frame").height();
      camera = new THREE.PerspectiveCamera(45, aspect, 1, 10000);
      camera.position.set(50, 80, 130);
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
      window.addEventListener("resize", onWindowResize, false);
      const ambientLight = new THREE.AmbientLight(0xcccccc, 0.4);
      scene.add(ambientLight);
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(1, 1, 0).normalize();
      scene.add(directionalLight);
      view.objects.map(drawNode);
      render();
    },
  });
}

function setNodePosition(node, properties) {
  node.scale.set(1, 1, 1);
  node.rotation.set(
    - Math.PI / 2, 0, 0
  );
  node.position.set(0, 0, 0);
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

function render() {
  if (renderer) renderer.render(scene, camera);
}

function onWindowResize() {
  camera.aspect = $(".main_frame").width() / $(".main_frame").height();
  camera.updateProjectionMatrix();
}

export function initViewBuilder() {
  Object.assign(action, {
    "View Properties": (viewObject) => showInstancePanel("node", viewObject.id),
    Connect: (viewObject) => showConnectionPanel(viewObject.device),
    Configuration: (viewObject) => showDeviceData(viewObject.device),
    "Run Service": (viewObject) => showRunServicePanel({ instance: viewObject.device }),
  });
  initLogicalFramework();
}
