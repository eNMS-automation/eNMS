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
