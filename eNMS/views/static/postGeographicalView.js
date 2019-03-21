/*
global
call: false
connectionParametersModal: false
deviceAutomationModal: false
createDevice: false
createLink: false
map: false
partial: false
selectedObject: false
showTypeModal: false
switchLayer: false
*/

$('#select-filters').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    deleteAll();
    objects.devices.map(createDevice);
    objects.links.map(createLink);
  });
});

const action = {
  'Export to Google Earth': partial(showModal, 'google-earth'),
  'Open Street Map': partial(switchLayer, 'osm'),
  'Google Maps': partial(switchLayer, 'gm'),
  'NASA': partial(switchLayer, 'nasa'),
  'Device properties': (d) => showTypeModal('device', d),
  'Link properties': (l) => showTypeModal('link', l),
  'Connect': connectionParametersModal,
  'Automation': deviceAutomationModal,
};

map.on('click', function(e) {
  selectedObject = null;
});

map.on('contextmenu', function() {
  if (!selectedObject) {
    $('.device-menu,.link-menu').hide();
    $('.global-menu').show();
  }
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/inventory/objects.html');
  $('#select-filters').change();
})();
