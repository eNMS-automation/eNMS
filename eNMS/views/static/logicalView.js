/*
global
alertify: false
call: false
d3: false
doc: false
graph: false
showTypeModal: false
*/

const width = 1200;
const height = 600;
let selectedDevices = [];

/**
 * Show device property modal.
 * @param {d} d - selected device.
 */
/*
function showNodeProperties(d) {
  showTypeModal('device', d.real_id);
}
*/

/**
 * Show link property modal.
 * @param {d} d - selected link.
 */
function showLinkProperties(d) {
  showTypeModal('link', d.real_id);
}

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    alertify.notify(`Filter applied.`, 'success', 5);
  });
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/logical_view.html');
})();
