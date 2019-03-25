/**
 * Display sites (pools with non-empty coordinates).
 */
function displaySites() { // eslint-disable-line no-unused-vars
  deleteAll();
  $('#map').css('visibility', 'visible');
  call('/get_all/pool', function(pools) {
    for (let i = 0; i < pools.length; i++) {
      if (pools[i].longitude) {
        createNode(pools[i], 'pool');
      }
    }
  });
  $('.menu,#pool-filter,#network').hide();
  $('.geo-menu,.rc-pool-menu').show();
  alertify.notify('Site view');
}

/**
 * Enter pool.
 * @param {poolId} poolId - Pool ID.
 */
function enterPool(poolId) { // eslint-disable-line no-unused-vars
  $('#map,#earth').css('visibility', 'hidden');
  $('.menu').hide();
  $('#network,.insite-menu,rc-device-menu,rc-link-menu').show();
  call(`/inventory/pool_objects/${poolId}`, function(objects) {
    alertify.notify('Loading the view...', 3);
    displayPool(objects.devices, objects.links);
  });
}

function updateView() {
  displaySites();
}

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
  'Display pools': displaySites,
  'Enter pool': enterPool,
};

$('#network').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selected);
  },
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/geographical_view.html');
  switchView('2D');
})();