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
 * Select devices in the scheduling modal.
 */
function sendSelection() {
  $('#devices').val(selectedDevices.map((s) => s[1].real_id));
}

/**
 * Select a device.
 * @param {d} d - selected device.
 */
function selectNode(d) {
  // we stop the propagation up the DOM tree so that the
  // unselectAll event bound to the canvas is not triggered
  d3.event.stopPropagation();
  // add both the HTML and graph elements in the selectedDevices array
  selectedDevices.push([this, d]);
  /*
  d3.select(this)
    .select('image')
    .attr('xlink:href', d.selected_img);
  sendSelection();
  */
  showTypeModal('device', d.real_id);
}

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

/**
 * Unselect all devices.
 */
function unselectAll() {
  d3.event.preventDefault();
  for (let i = 0; i < selectedDevices.length; i++) {
    d3.select(selectedDevices[i][0])
      .select('image')
      .attr('xlink:href', selectedDevices[i][1].img);
  }
  selectedDevices = [];
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
  .charge(-1000)
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
  .on('click', showLinkProperties);

let node = container.selectAll('.node')
  .data(graph.nodes)
  .enter().append('g')
  .attr('class', 'node')
  .call(force.drag)
  .on('click', selectNode);

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
    return d['name'];
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
  call(`/objects/pool_objects/${this.value}`, function(objects) {
    let devicesId = objects.devices.map((n) => n.id);
    let linksId = objects.links.map((l) => l.id);
    node.style('visibility', function(d) {
      return devicesId.includes(d.real_id) ? 'visible' : 'hidden';
    });
    link.style('visibility', function(d) {
      return linksId.includes(d.real_id) ? 'visible' : 'hidden';
    });
    alertify.notify(`Filter applied.`, 'success', 5);
  });
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/logical_view.html');
})();
