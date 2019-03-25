/*
global
enterPool: false
L: false
link_colors: false
parameters: false
showTypeModal: false
subtype_sizes: false
view: false
WE: false
*/

const routerIcon = window['icon_router'];

function updateView() {
  $('#pool-filter').change();
}

$('#pool-filter').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    deleteAll();
    objects.devices.map((d) => createNode(d, 'device'));
    objects.links.map(createLink);
    if (view == '2DC') {
      map.addLayer(markers);
    }
  });
});

const action = {
  'Export to Google Earth': partial(showModal, 'google-earth'),
  'Open Street Map': partial(switchLayer, 'osm'),
  'Google Maps': partial(switchLayer, 'gm'),
  'NASA': partial(switchLayer, 'nasa'),
  'Device properties': (d) => showTypeModal('device', d),
  'Link properties': (l) => showTypeModal('link', l),
  'Pool properties': (p) => showTypeModal('pool', p),
  'Connect': connectionParametersModal,
  'Automation': deviceAutomationModal,
};

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/geographical_view.html');
  $('#network').hide();
  updateView();
})();
