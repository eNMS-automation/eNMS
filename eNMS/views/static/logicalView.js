/*
global
alertify: false
call: false
connectionParametersModal: false
deviceAutomationModal: false
doc: false
showTypeModal: false
*/

let selectedObject;

const networkAction = {
  'Device properties': (d) => showTypeModal('device', d),
  'Link properties': (l) => showTypeModal('link', l),
  'Connect': connectionParametersModal,
  'Automation': deviceAutomationModal,
  'Not implemented yet': () => alertify.notify('Later.'),
};
