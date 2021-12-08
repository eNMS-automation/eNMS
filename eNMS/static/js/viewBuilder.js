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

let currentView;
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
}

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

function openDeletionPanel() {
}

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
  updateRightClickBindings();
}

export function viewCreation(instance) {
  if (instance.id == currentView.id) {
    $("#current-view option:selected").text(instance.name).trigger("change");
  } else {
    $("#current-view").append(
      `<option value="${instance.id}">${instance.name}</option>`
    );
    $("#current-view").val(instance.id).trigger("change");
    displayView();
  }
}
