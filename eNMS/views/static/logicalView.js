/*
global
alertify: false
vis: false
*/

let container = document.getElementById("network");
let selected; // eslint-disable-line no-unused-vars
let network; // eslint-disable-line no-unused-vars

/**
 * Convert device to Vis node.
 * @param {device} device - Device.
 * @return {node}
 */
function deviceToNode(device) {
  return {
    id: device.id,
    label: device.name,
    image: `../views/static/images/2D/${device.subtype}.gif`,
    shape: "image",
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
    from: link.source_id,
    to: link.destination_id,
  };
}

/**
 * Erase the network.
 */
// eslint-disable-next-line
function eraseNetwork() {
  network = new vis.Network(container);
}

/**
 * Display a pool.
 * @param {nodes} nodes - Array of nodes to display.
 * @param {edges} edges - Array of edges to display.
 */
// eslint-disable-next-line
function displayPool(nodes, edges) {
  nodes = new vis.DataSet(nodes.map(deviceToNode));
  edges = new vis.DataSet(edges.map(linkToEdge));
  const network = new vis.Network(
    container,
    { nodes: nodes, edges: edges },
    {}
  );
  network.on("oncontext", function(properties) {
    properties.event.preventDefault();
    const node = this.getNodeAt(properties.pointer.DOM);
    const edge = this.getEdgeAt(properties.pointer.DOM);
    if (typeof node !== "undefined") {
      $(".menu").hide();
      $(".rc-device-menu").show();
      selected = node;
    } else if (typeof edge !== "undefined") {
      selected = edge;
      $(".menu").hide();
      $(".rc-link-menu").show();
    } else {
      $(".menu").hide();
      $(".insite-menu").show();
    }
  });
  alertify.notify(
    `Loading the view...<br/>
    Scroll to zoom in/out. Right-click on a node to display the menu.`
  );
}
