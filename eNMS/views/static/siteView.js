/**
 * Display pools.
 */
function displayPools() { // eslint-disable-line no-unused-vars
  viewMode = 'site';
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
 * Display network.
 */
function displayNetwork() { // eslint-disable-line no-unused-vars
  viewMode = 'network';
  $('#pool-filter').change();
  $('#map').css('visibility', 'visible');
  $('.menu,#network').hide();
  $('.geo-menu,#pool-filter').show();
  alertify.notify('Network view.');
}

/**
 * Enter pool.
 * @param {poolId} poolId - Pool ID.
 */
function enterPool(poolId) { // eslint-disable-line no-unused-vars
  viewMode = 'insite';
  $('#map').css('visibility', 'hidden');
  $('.menu').hide();
  $('#network,.insite-menu,rc-device-menu,rc-link-menu').show();
  call(`/inventory/pool_objects/${poolId}`, function(objects) {
    alertify.notify('Loading the view...', 3);
    displayPool(objects.devices, objects.links);
  });
}