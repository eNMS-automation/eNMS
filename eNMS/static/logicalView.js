/*
global
action: false
alertify: false
call: false
jsPanel: false
vis: false
*/

let selected; // eslint-disable-line no-unused-vars

/**
 * Convert device to Vis node.
 * @param {device} device - Device.
 * @return {node}
 */
function deviceToNode(device) {
  return {
    id: device.id,
    label: device.name,
    image: `/static/images/2D/${device.subtype}.gif`,
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
 * Visualize pool.
 * @param {id} id - Id of the pool.
 */
// eslint-disable-next-line
function showPoolView(poolId) {
  jsPanel.create({
    id: `pool-view-${poolId}`,
    theme: "none",
    border: "medium",
    headerTitle: "Pool view",
    position: "center-top 0 58",
    contentSize: "1000 600",
    content:
      `<div id="network-${poolId}" style="height:100%; width:100%;"></div>`,
    dragit: {
      opacity: 0.7,
      containment: [5, 5, 5, 5],
    },
  });
  call(`/get-pool-${poolId}`, function(pool) {
    $(`#network-${poolId}`).contextMenu({
      menuSelector: "#contextMenu",
      menuSelected: function(invokedOn, selectedMenu) {
        const row = selectedMenu.text();
        action[row](selected);
      },
    });
    displayPool(poolId, pool.devices, pool.links);
  });
}

/**
 * Display a pool.
 * @param {nodes} nodes - Array of nodes to display.
 * @param {edges} edges - Array of edges to display.
 */
// eslint-disable-next-line
function displayPool(poolId, nodes, edges) {
  let container = document.getElementById(`network-${poolId}`);
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
