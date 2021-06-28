/*
global
action: false
CSS2DObject: false
CSS2DRenderer: false
page: false
THREE: false
TransformControls: false
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
  setTriggerMenu,
  showInstancePanel,
} from "./base.js";
import { showConnectionPanel, showDeviceData } from "./inventory.js";

let selectedObject;
let currentMode = "select";
let currentView;
let selectedObjects = [];
let camera;
let scene;
let renderer;
let controls;
let transformControls;
let labelRenderer;
let nodes = {};
let pointer;
let activeControls = false;
let raycaster;
let texture;
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
      selectedObject = [];
      currentView = view;
      const aspect = $(".main_frame").width() / $(".main_frame").height();
      camera = new THREE.PerspectiveCamera(45, aspect, 1, 10000);
      raycaster = new THREE.Raycaster();
      pointer = new THREE.Vector2();
      camera.position.set(500, 800, 1300);
      camera.lookAt(0, 0, 0);
      scene = new THREE.Scene();
      scene.background = new THREE.Color(0xffffff);
      labelRenderer = new CSS2DRenderer();
      labelRenderer.setSize($(".main_frame").width(), $(".main_frame").height());
      labelRenderer.domElement.style.position = "absolute";
      const container = document.getElementById("map");
      $("#map").empty();
      renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setPixelRatio(window.devicePixelRatio);
      renderer.setSize($(".main_frame").width(), $(".main_frame").height());
      container.appendChild(labelRenderer.domElement);
      container.appendChild(renderer.domElement);
      controls = new THREE.OrbitControls(camera, labelRenderer.domElement);
      controls.addEventListener("change", render);
      controls.maxPolarAngle = Math.PI / 2;
      container.addEventListener("mousedown", onMouseDown, false);
      container.addEventListener("mousemove", onMouseMove, false);
      window.addEventListener("resize", onWindowResize, false);
      transformControls = new TransformControls(camera, labelRenderer.domElement);
      transformControls.addEventListener("change", render);
      transformControls.addEventListener("dragging-changed", function (event) {
        if (!event.value) savePositions();
        controls.enabled = !event.value;
      });
      transformControls.addEventListener("mouseUp", function () {
        activeControls = false;
      });
      transformControls.addEventListener("mouseDown", function () {
        activeControls = true;
      });
      const ambientLight = new THREE.AmbientLight(0xcccccc, 0.4);
      scene.add(ambientLight);
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
      directionalLight.position.set(1, 1, 0).normalize();
      scene.add(directionalLight);
      scene.add(transformControls);
      updateRightClickBindings(controls);
      view.objects.map(drawNode);
      switchMode("select");
      render();
    },
  });
}

function onMouseDown(event) {
  const intersects = getIntersects(event);
  if (intersects.length > 0) {
    let object = intersects[0].object;
    selectedObject = object.userData;
    if (selectedObject.type == "node") {
      selectedObject = { id: selectedObject.device_id, type: "device" };
    }
    if (object.userData.type == "collada") {
      object = daeModels[object.userData.id];
      selectedObjects.push(object);
      transformControls.attach(...object.children);
    } else {
      if (currentMode == "select") {
        object.material.color.set(0xff0000);
        selectedObjects.push(object);
      } else if (!activeControls && object !== transformControls.object) {
        transformControls.attach(object);
      }
    }
  } else {
    activeControls = false;
    transformControls.detach(transformControls.object);
    selectedObjects.map((object) => {
      object.material.color.set(0xffffff);
    });
    selectedObjects = [];
  }
  setTriggerMenu(true);
  if (!intersects.length) {
    $(".rc-object-menu").hide();
    $(".global").show();
  } else {
    $(".global").hide();
    $(".rc-object-menu").show();
  }
  render();
}

function createPlan() {
  call({
    url: `/create_view_object/plan/${currentView.id}`,
    form: "plan-form",
    callback: function (result) {
      currentView.last_modified = result;
      drawNode(result.node);
      $("#plan").remove();
    },
  });
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
        { position: node.position, scale: node.scale },
      ])
    ),
    callback: function (updateTime) {
      if (updateTime) currentView.last_modified = updateTime;
    },
  });
}

function switchMode(mode) {
  $(`#btn-${currentMode},#btn-${mode}`).toggleClass("active");
  currentMode = mode;
  transformControls.enabled = mode != "select";
  if (mode == "select") {
    scene.remove(transformControls);
    transformControls.detach();
  } else {
    scene.add(transformControls);
    transformControls.setMode(mode);
  }
}

function drawNode(node) {
  let geometry;
  let material;
  if (node.type == "plan") {
    geometry = new THREE.BoxGeometry(1000, 1000, 8);
    material = new THREE.MeshBasicMaterial({ map: texture });
  } else if (node.type == "label") {
    geometry = new THREE.SphereGeometry(5, 32, 32);
    material = new THREE.MeshBasicMaterial({
      transparent: true,
      opacity: 0.3,
    });
  } else {
    if (node.model) {
      new THREE.ColladaLoader().load(
        `/static/img/view/models/${node.model}.dae`,
        function (collada) {
          daeModels[node.id] = collada.scene;
          daeModels[node.id].scale.set(10, 10, 10);
          daeModels[node.id].position.set(
            node.position_x,
            node.position_y,
            node.position_z
          );
          daeModels[node.id].traverse(function (child) {
            child.userData = { type: "collada", id: node.id };
          });
          scene.add(daeModels[node.id]);
        }
      );
      return;
    } else {
      material = new THREE.MeshBasicMaterial({
        color: 0x3c8c8c,
        opacity: 0.8,
        transparent: true,
      });
      geometry = new THREE.CylinderGeometry(30, 30, 20, 32);
    }
  }
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(node.position_x, Math.max(node.position_y, 10), node.position_z);
  if (node.type == "plan") {
    mesh.rotation.x = Math.PI / 2;
  } else {
    drawLabel(node, mesh);
  }
  nodes[node.id] = mesh;
  mesh.userData = node;
  scene.add(mesh);
}

function getIntersects(event) {
  const menuWidth = $(".left_column").is(":visible") ? $(".left_column").width() : 0;
  const width = ((event.clientX - menuWidth - 15) / $(".main_frame").width()) * 2 - 1;
  const height = -((event.clientY - 70) / $(".main_frame").height()) * 2 + 1;
  pointer.set(width, height);
  raycaster.setFromCamera(pointer, camera);
  return raycaster.intersectObjects(scene.children, true);
}

function onMouseMove(event) {
  setTriggerMenu(false);
  const intersects = getIntersects(event);
  document.body.style.cursor = intersects.length > 0 ? "pointer" : "default";
}

function drawLabel(node, mesh) {
  const div = document.createElement("div");
  div.className = "label";
  const style = { marginTop: "-1em", color: "#FF0000" };
  div.textContent = node.type == "label" ? node.text : node.name;
  Object.assign(div.style, style);
  const labelObject = new CSS2DObject(div);
  labelObject.position.set(0, 0, 0);
  mesh.add(labelObject);
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

export function viewCreation(view) {
  if (view.id == currentView.id) {
    $("#current-view option:selected").text(view.name).trigger("change");
  } else {
    $("#current-view").append(`<option value="${view.id}">${view.name}</option>`);
    $("#current-view").val(view.id).trigger("change");
    displayView();
  }
}

function createLabel() {
  call({
    url: `/create_view_object/label/${currentView.id}`,
    form: "view_label-form",
    callback: function (result) {
      $("#view_label").remove();
      drawNode(result.node);
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
      result.nodes.map(drawNode);
      notify("Objects successfully added to the view.", "success", 5);
    },
  });
}

function updateRightClickBindings(controls) {
  Object.assign(action, {
    "Add to View": addObjectPanel,
    "Create View": () => createNewView("create"),
    "Create Label": () => openPanel({ name: "view_label", title: "Create New Label" }),
    "Create Plan": () => openPanel({ name: "plan", title: "Create New Plan" }),
    "Edit View": () => createNewView("edit"),
    "Edit Pool": () => showInstancePanel("pool", currentPath),
    Delete: () => deleteSelection(),
    "Duplicate View": () => createNewView("duplicate"),
    "Switch Mode": switchMode,
    "Zoom In": () => controls?.dollyOut(),
    "Zoom Out": () => controls?.dollyIn(),
    Backward: () => displayView({ direction: "left" }),
    Forward: () => displayView({ direction: "right" }),
  });
}

function render() {
  if (renderer && labelRenderer) {
    renderer.render(scene, camera);
    labelRenderer.render(scene, camera);
  }
}

function onWindowResize() {
  camera.aspect = $(".main_frame").width() / $(".main_frame").height();
  camera.updateProjectionMatrix();
  labelRenderer.setSize($(".main_frame").width(), $(".main_frame").height());
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
    Properties: (o) => showInstancePanel(o.type, o.id),
    Connect: (d) => showConnectionPanel(d),
    Configuration: (d) => showDeviceData(d),
    "Run Service": (d) => showRunServicePanel({ instance: d }),
  });
  initLogicalFramework();
}

function animate() {
  requestAnimationFrame(animate);
  render();
}

animate();

configureNamespace("viewBuilder", [addObjectsToView, createLabel, createPlan]);
