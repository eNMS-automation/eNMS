/*
global
alertify: false
call: false
connectionParametersModal: false
deviceAutomationModal: false
doc: false
showTypeModal: false
*/

let selected;

const action = {
  'Device properties': (d) => showTypeModal('device', d),
  'Link properties': (l) => showTypeModal('link', l),
  'Connect': connectionParametersModal,
  'Automation': deviceAutomationModal,
  'Not implemented yet': () => alertify.notify('Later.'),
};

$('#network').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selected);
  },
});

$('#select-filters').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    displayNetwork(objects.devices, objects.links);
  });
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/logical_view.html');
  $('#select-filters').change();
})();
