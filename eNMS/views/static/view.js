/*
global
vis: false
*/

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

let container = document.getElementById('network');

/**
 * Display a pool.
 * @param {nodes} nodes - Array of nodes to display.
  * @param {edges} edges - Array of edges to display.
 */
function displayPool(nodes, edges) {
  nodes = new vis.DataSet(nodes.map(deviceToNode));
  edges = new vis.DataSet(edges.map(linkToEdge));
  const network = new vis.Network(container, {nodes: nodes, edges: edges}, {});
  network.on('oncontext', function(properties) {
    properties.event.preventDefault();
    const node = this.getNodeAt(properties.pointer.DOM);
    const edge = this.getEdgeAt(properties.pointer.DOM);
    if (typeof node !== 'undefined') {
      $('.global-menu,.rc-link-menu').hide();
      $('.rc-link-menu').show();
      selected = node;
    } else if (typeof edge !== 'undefined') {
      selected = edge;
      $('.global-menu,.rc-link-menu').hide();
      $('.rc-link-menu').show();
    } else {
      $('.rc-link-menu,.rc-link-menu').hide();
      $('.global-menu').show();
    }
  });
}