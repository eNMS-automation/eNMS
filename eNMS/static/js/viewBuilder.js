/*
global
action: false
page: false
*/

import {
  call,
  history,
  historyPosition,
  moveHistory,
  notify,
  showInstancePanel,
} from "./base.js";

let ctrlKeyPressed;
let currentView;
export let currentPath = localStorage.getItem("path");
export let view = JSON.parse(localStorage.getItem("view"));

function switchToView({ path, direction } = {}) {
  if (typeof path === "undefined") return;
  if (path.toString().includes(">")) {
    $("#up-arrow").removeClass("disabled");
  } else {
    $("#up-arrow").addClass("disabled");
  }
  currentPath = path;
  localStorage.setItem(page, currentPath);
  moveHistory(path, direction);
  const [viewId] = currentPath.split(">").slice(-1);
  if (!path && page == "object_table") {
    $("#view-filtering").val("");
    tableInstances["object"].table.page(0).ajax.reload(null, false);
    return;
  }
  call({
    url: `/get/view/${viewId}`,
    callback: function (view) {
      currentView = view;
      if (page == "view_builder") {
        if (view) localStorage.setItem("view", JSON.stringify(view));
        displayView(view);
      } else {
        $("#view-filtering").val(path ? view.name : "");
        tableInstances["object"].table.page(0).ajax.reload(null, false);
      }
    },
  });
};

function createNewView(mode) {
  if (mode == "create_view") {
    showInstancePanel("view");
  } else if (!currentView) {
    notify("No view has been created yet.", "error", 5);
  } else if (mode == "duplicate_view") {
    showInstancePanel("view", currentView.id, "duplicate");
  } else {
    showInstancePanel("view", currentView.id);
  }
}

function openDeletionPanel() {}

function updateRightClickBindings() {
  Object.assign(action, {
    "Create View": () => createNewView("create_view"),
    "Duplicate View": () => createNewView("duplicate_view"),
    "Edit View": () => showInstancePanel("view", view.id),
    Delete: openDeletionPanel,
    "Create Label": () => showLabelPanel({ usePosition: true }),
    "Create Label Button": () => showLabelPanel({ usePosition: false }),
    "Edit Label": (label) => showLabelPanel({ label: label, usePosition: true }),
    "Edit Edge": (edge) => {
      showInstancePanel("link", edge.id);
    },
    Skip: () => skipServices(),
    "Zoom In": () => graph.zoom(0.2),
    "Zoom Out": () => graph.zoom(-0.2),
    "Enter View": (node) => switchToView(`${currentPath}>${node.id}`),
    Backward: () => switchToView(history[historyPosition - 1], "left"),
    Forward: () => switchToView(history[historyPosition + 1], "right"),
    Upward: () => {
      const parentPath = currentPath.split(">").slice(0, -1).join(">");
      if (parentPath) switchToView(parentPath);
    },
  });
  $("#network").contextMenu({
    menuSelector: "#contextMenu",
    menuSelected: function (selectedMenu) {
      const row = selectedMenu.text();
      action[row](selectedObject);
    },
  });
}

export function initViewBuilder() {
  window.onkeydown = () => {
    ctrlKeyPressed = true;
  };
  window.onkeyup = () => {
    ctrlKeyPressed = false;
  };
  vis.Network.prototype.zoom = function (scale) {
    const animationOptions = {
      scale: this.getScale() + scale,
      animation: { duration: 300 },
    };
    this.view.moveTo(animationOptions);
  };
  $("#left-arrow,#right-arrow").addClass("disabled");
  call({
    url: "/get_top_level_instances/view",
    callback: function (views) {
      views.sort((a, b) => a.name.localeCompare(b.name));
      for (let i = 0; i < views.length; i++) {
        $("#current-view").append(
          `<option value="${views[i].id}">${views[i].name}</option>`
        );
      }
      if (currentPath && views.some((w) => w.id == currentPath.split(">")[0])) {
        $("#current-view").val(currentPath.split(">")[0]);
        switchToView(currentPath);
      } else {
        view = $("#current-view").val();
        if (view) {
          switchToView(view);
        } else {
          notify("No view has been created yet.", "error", 5);
        }
      }
      $("#current-view").selectpicker({ liveSearch: true });
    },
  });
  updateRightClickBindings();
}

export function viewCreation(instance) {
  if (instance.id == currentView?.id) {
    $("#current-view option:selected").text(instance.name).trigger("change");
  } else {
    $("#current-view").append(
      `<option value="${instance.id}">${instance.name}</option>`
    );
    $("#current-view").val(instance.id).trigger("change");
    displayView();
  }
}
