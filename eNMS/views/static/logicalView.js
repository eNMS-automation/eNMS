/*
global
alertify: false
d3: false
graph: false
partial: false
showModal: false
showObjectModal: false
*/

const width = 960;
const height = 500;
let selectedNodes = [];

/**
 * Select devices in the scheduling modal.
 */
function sendSelection() {
  $('#devices').val(selectedNodes.map((s) => s[1].real_id));
}

/**
 * Select a device.
 * @param {d} d - selected device.
 */
function selectNode(d) {
  // we stop the propagation up the DOM tree so that the
  // unselectAll event bound to the canvas is not triggered
  d3.event.stopPropagation();
  // add both the HTML and graph elements in the selectedNodes array
  selectedNodes.push([this, d]);
  d3.select(this)
    .select('image')
    .attr('xlink:href', d.selected_img);
  sendSelection();
}

/**
 * Show device property modal.
 * @param {d} d - selected device.
 */
function showNodeProperties(d) {
  showObjectModal('device', d.real_id);
}

/**
 * Show link property modal.
 * @param {d} d - selected link.
 */
function showLinkProperties(d) {
  showObjectModal('link', d.real_id);
}

/**
 * Unselect all devices.
 */
function unselectAll() {
  d3.event.preventDefault();
  for (let i = 0; i < selectedNodes.length; i++) {
    d3.select(selectedNodes[i][0])
      .select('image')
      .attr('xlink:href', selectedNodes[i][1].img);
  }
  selectedNodes = [];
  sendSelection();
}

let zoom = d3.behavior.zoom()
  .scaleExtent([1, 50])
  .on('zoom', zoomed);

let svg = d3.select('#logical_view').append('svg')
  .attr('width', width)
  .attr('height', height)
  .on('click', unselectAll)
  .call(zoom)
  .on('mousedown.zoom', null);

let force = d3.layout.force()
  .gravity(0.2)
  .distance(10)
  .charge(-100)
  .size([width, height]);

force
  .nodes(graph.nodes)
  .links(graph.links)
  .start();

let container = svg.append('g');

let link = container.selectAll('.link')
  .data(graph.links)
  .enter().append('line')
  .attr('class', 'link')
  .on('dblclick', showLinkProperties);

let node = container.selectAll('.node')
  .data(graph.nodes)
  .enter().append('g')
  .attr('class', 'node')
  .call(force.drag)
  .on('click', selectNode)
  .on('dblclick', showNodeProperties);

/**
 * Zoom with scroll.
 */
function zoomed() {
  container.attr(
    'transform',
    'translate(' + d3.event.translate + ')scale(' + d3.event.scale + ')'
  );
}

node.append('image')
  .attr('xlink:href', function(d) {
    return d.img;
  })
  .attr('x', -8)
  .attr('y', -8)
  .attr('width', 16)
  .attr('height', 16);

node.append('text')
  .attr('dx', 8)
  .attr('dy', '.35em')
  .text(function(d) {
    return d.name;
  });

force.on('tick', function() {
  link
    .attr('x1', function(d) {
      return d.source.x;
    })
    .attr('y1', function(d) {
      return d.source.y;
    })
    .attr('x2', function(d) {
      return d.target.x;
    })
    .attr('y2', function(d) {
      return d.target.y;
    });
  node.attr('transform', function(d) {
    return 'translate(' + d.x + ',' + d.y + ')';
  });
});

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
  $.ajax({
    type: 'POST',
    url: `/objects/pool_objects/${this.value}`,
    dataType: 'json',
    success: function(objects) {
      let devicesId = objects.devices.map((n) => n.id);
      let linksId = objects.links.map((l) => l.id);
      node.style('visibility', function(d) {
        return devicesId.includes(d.real_id.toString()) ? 'visible' : 'hidden';
      });
      link.style('visibility', function(d) {
        return linksId.includes(d.real_id.toString()) ? 'visible' : 'hidden';
      });
      alertify.notify(`Filter applied.`, 'success', 5);
    },
  });
});

let action = {
  'Parameters': partial(showModal, 'filters'),
  'Add new task': partial(showModal, 'scheduling'),
};

$('#logical_view').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    let row = selectedMenu.text();
    action[row]();
  },
});
