/*
global
alertify: false
call: false
doc: false
*/

let selected;

function deviceToNode(device) {
  return {
    id: device.id,
    label: device.name,
    image: `static/images/default/${device.subtype}.gif`,
    shape: 'image'
  };
}

function linkToEdge(link) {
  return {
    id: link.id,
    from: link.source.id,
    to: link.destination.id,
  };
}

var nodes = new vis.DataSet(devices.map(deviceToNode));
var edges = new vis.DataSet(links.map(linkToEdge));

var container = document.getElementById('logical_view');
var data = {
  nodes: nodes,
  edges: edges,
};
var options = {};
var network = new vis.Network(container, data, options);

network.on('oncontext', function(properties) {
  properties.event.preventDefault();
  const node = this.getNodeAt(properties.pointer.DOM);
  const edge = this.getEdgeAt(properties.pointer.DOM);
  if (typeof node !== 'undefined') {
    $('.global-menu,.link-menu').hide();
    $('.device-menu').show();
    selected = node;
  }
  else if (typeof edge !== 'undefined') {
    selected = edge;
    $('.global-menu,.device-menu').hide();
    $('.link-menu').show();
  } else {
    $('.link-menu,.device-menu').hide();
    $('.global-menu').show();
  }
});

const action = {
  'Device properties': (d) => showTypeModal('device', d),
  'Link properties': (l) => showTypeModal('link', l),
  'Connect': connectionParametersModal,
  'Automation': deviceAutomationModal,
  'Not implemented yet': () => alertify.notify('Later.'),
};

$('#logical_view').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selected);
  },
});

$('#select-filters').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    alertify.notify(`Filter applied.`, 'success', 5);
  });
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/logical_view.html');
})();
