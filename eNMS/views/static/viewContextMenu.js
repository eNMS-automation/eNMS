/*
global
partial: false
showTypeModal: false
*/

const action = {
  'Export to Google Earth': partial(showModal, 'google-earth'),
  'Open Street Map': partial(switchLayer, 'osm'),
  'Google Maps': partial(switchLayer, 'gm'),
  'NASA': partial(switchLayer, 'nasa'),
  'Properties': (d) => showTypeModal('device', d),
  'Connect': connectionParametersModal,
  'Automation': deviceAutomationModal,
  'Delete': (d) => confirmDeletion('device', d),
};