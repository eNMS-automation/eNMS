import * as administrationController from "./administration.js";
import * as baseController from "./base.js";
import * as automationController from "./automation.js";
import * as workflowController from "./workflow.js";
import * as inventoryController from "./inventory.js";

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
};

window.eNMS = {
  copyToClipboard: baseController.copyToClipboard,
  displayFiles: administrationController.displayFiles,
  exportTopology: administrationController.exportTopology,
  filterTable: baseController.filterTable,
  fullScreen: fullScreen,
  getWorkflowState: workflowController.getWorkflowState,
  normalRun: automationController.normalRun,
  processData: baseController.processData,
  refreshTable: baseController.refreshTable,
  showPanel: baseController.showPanel,
  showTypePanel: baseController.showTypePanel,
  showDeviceNetworkData: inventoryController.showDeviceNetworkData,
  showRuntimePanel: inventoryController.showRuntimePanel,
  sshConnection: inventoryController.sshConnection,
  switchToWorkflow: automationController.switchToWorkflow,
};
