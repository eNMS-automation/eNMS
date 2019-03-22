/*
global
alertify: false
call: false
connectionParametersModal: false
createDevice: false
createLink: false
deleteAll: false
deviceAutomationModal: false
doc: false
map: false
partial: false
selectedObject: true
showModal: false
showTypeModal: false
switchLayer: false
*/

let viewMode = 'network';

/**
 * Display pools.
 */
function displayPools() { // eslint-disable-line no-unused-vars
  deleteAll();
  pools.map((p) => {
    if (p.device_longitude && p.device_latitude) {
      createNode(p, nodeType='pool')
    }
  });
  viewMode = 'site';
  $('.menu,#select-filters').hide();
  $('.global-site-menu,.pool-menu').show();
  alertify.notify('Switch to Pool View');
}

/**
 * Display network.
 */
function displayNetwork() { // eslint-disable-line no-unused-vars
  viewMode = 'network';
  $('#select-filters').change();
  $('#select-filters').show();
}


$('#select-filters').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    deleteAll();
    objects.devices.map((d) => createNode(d, nodeType='device'));
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
  'Display pools': displayPools,
  'Display network': displayNetwork,
};

map.on('click', function(e) {
  selectedObject = null;
});

map.on('contextmenu', function() {
  if (!selectedObject) {
    $('.menu').hide();
    $(`.global-menu,.${viewMode}-menu`).show();
  }
});

$('.dropdown-submenu a.menu-submenu').on('click', function(e) {
  $(this).next('ul').toggle();
  e.stopPropagation();
  e.preventDefault();
});

$('body').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selectedObject);
    selectedObject = null;
  },
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/geographical_view.html');
  $('#select-filters').change();
})();
