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
  showInstancePanel,
} from "./base.js";
import { showConnectionPanel, showDeviceData } from "./inventory.js";

let currentView;
let camera;
let scene;
let renderer;
let nodes = {};

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

