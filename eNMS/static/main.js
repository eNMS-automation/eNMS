import { displayFiles } from './administration.js';
import { filterTable, processData, refreshTable, showPanel, showTypePanel } from './base.js';
import { showDeviceNetworkData } from './inventory.js';

const fullScreen = function() {
  if (
    document.fullscreenElement ||
    document.webkitFullscreenElement ||
    document.mozFullScreenElement ||
    document.msFullscreenElement
  ) {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.mozCancelFullScreen) {
      document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
  } else {
    const element = $("#container-body").get(0);
    if (element.requestFullscreen) {
      element.requestFullscreen();
    } else if (element.mozRequestFullScreen) {
      element.mozRequestFullScreen();
    } else if (element.webkitRequestFullscreen) {
      element.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
    } else if (element.msRequestFullscreen) {
      element.msRequestFullscreen();
    }
  }
}

window.eNMS = {
  displayFiles: displayFiles,
  filterTable: filterTable,
  fullScreen: fullScreen,
  processData: processData,
  refreshTable: refreshTable,
  showPanel: showPanel,
  showTypePanel: showTypePanel,
  showDeviceNetworkData: showDeviceNetworkData
}