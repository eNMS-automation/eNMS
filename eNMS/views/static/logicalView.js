/*
global
alertify: false
call: false
connectionParametersModal: false
deviceAutomationModal: false
devices: false
doc: false
links: false
showTypeModal: false
vis: false
*/

let selected;

/**
 * Convert device to Vis node.
 * @param {device} device - Device.
 * @return {node}
 */
function deviceToNode(device) {
  return {
    id: device.id,
    label: device.name,
    image: `static/images/default/${device.subtype}.gif`,
    shape: 'image',
  };
}

/**
 * Convert link to Vis edge.
 * @param {link} link - Link.
 * @return {edge}
 */
function linkToEdge(link) {
  return {
    id: link.id,
    from: link.source.id,
    to: link.destination.id,
  };
}

let nodes;
let edges;
let container = document.getElementById('logical_view');

function displayWorkflow(nodes, edges) {
  nodes = new vis.DataSet(nodes.map(deviceToNode));
  edges = new vis.DataSet(edges.map(linkToEdge));
  network = new vis.Network(container, {nodes: nodes, edges: edges}, {});
  network.on('oncontext', function(properties) {
    properties.event.preventDefault();
    const node = this.getNodeAt(properties.pointer.DOM);
    const edge = this.getEdgeAt(properties.pointer.DOM);
    if (typeof node !== 'undefined') {
      $('.global-menu,.link-menu').hide();
      $('.device-menu').show();
      selected = node;
    } else if (typeof edge !== 'undefined') {
      selected = edge;
      $('.global-menu,.device-menu').hide();
      $('.link-menu').show();
    } else {
      $('.link-menu,.device-menu').hide();
      $('.global-menu').show();
    }
  });
}

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
    displayWorkflow(objects.devices, objects.links);
    alertify.notify(`Filter applied.`, 'success', 5);
  });
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/logical_view.html');
})();
