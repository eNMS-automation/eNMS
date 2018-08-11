/*
global
alertify: false
d3: false
graph: false
partial: false
showModal: false
showObjectModal: false
*/

let selectedNodes = [];

/**
 * Select nodes in the scheduling modal.
 */
function sendSelection() {
  $('#nodes').val(selectedNodes.map((s) => s[1].real_id));
}

/**
 * Select a node.
 * @param {d} d - selected node.
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
 * Show node property modal.
 * @param {d} d - selected node.
 */
function showNodeProperties(d) {
  showObjectModal('node', d.real_id);
}

/**
 * Show link property modal.
 * @param {d} d - selected link.
 */
function showLinkProperties(d) {
  showObjectModal('link', d.real_id);
}

/**
 * Unselect all nodes.
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

const width = 960;
const height = 500;

let zoom = d3.behavior.zoom()
  .scaleExtent([1, 50])
  .on('zoom', zoomed);

let svg = d3.select('#logical_view').append('svg')
  .attr('width', width)
  .attr('height', height)
  .on('click', unselectAll)
  .call(zoom)
  .on('mousedown.zoom', null);

/**
 * Rectangular selection.
 * @param {x} x
 * @param {x} y
 * @param {w} w
 * @param {h} h
 */
function rect(x, y, w, h) {
  return 'M' + [x, y] + ' l' + [w, 0] + ' l' + [0, h] + ' l' + [-w, 0] + 'z';
}

let selection = svg.append('path')
  .attr('class', 'selection')
  .attr('visibility', 'hidden');

let startSelection = function(start) {
  selection
    .attr('d', rect(start[0], start[0], 0, 0))
    .attr('visibility', 'visible');
};

let moveSelection = function(start, moved) {
  selection.attr('d', rect(
    start[0],
    start[1],
    moved[0] - start[0],
    moved[1] - start[1]
  ));
};

let endSelection = function(start, end) {
  const minX = Math.min(start[0], end[0]);
  const maxX = Math.max(start[0], end[0]);
  const minY = Math.min(start[1], end[1]);
  const maxY = Math.max(start[1], end[1]);
  selection.attr('visibility', 'hidden');
  // select all nodes in the rectangle
  d3.selectAll('.node')
    .each(function(d) {
      if (minX <= d.x && d.x <= maxX && minY <= d.y && d.y <= maxY) {
        selectedNodes.push([this, d]);
        d3.select(this)
          .select('image')
          .attr('xlink:href', d.selected_img);
      }
    });
  sendSelection();
};

svg.on('mousedown', function() {
  // same binding as leaflet: shift + left-click button for selection
  if (
    !d3.event.shiftKey
    || ((d3.event.which !== 1) && (d3.event.button !== 1))
  ) {
    return false;
  }
  let subject = d3.select(window);
  let parent = this.parentNode;
  let start = d3.mouse(parent);
  startSelection(start);
  subject
    .on('mousemove.selection', function() {
      moveSelection(start, d3.mouse(parent));
    })
    .on('mouseup.selection', function() {
      endSelection(start, d3.mouse(parent));
      subject
        .on('mousemove.selection', null)
        .on('mouseup.selection', null);
    });
});

svg.on('touchstart', function() {
    const subject = d3.select(this);
    const parent = this.parentNode;
    const id = d3.event.changedTouches[0].identifier;
    const start = d3.touch(parent, id);
    let pos;
    startSelection(start);
    subject
      .on('touchmove.'+id, function() {
        if (pos = d3.touch(parent, id)) {
          moveSelection(start, pos);
        }
      })
      .on('touchend.'+id, function() {
        if (pos = d3.touch(parent, id)) {
          endSelection(start, pos);
          subject
            .on('touchmove.'+id, null)
            .on('touchend.'+id, null);
        }
      });
});

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
      let nodesId = objects.nodes.map((n) => n.id);
      let linksId = objects.links.map((l) => l.id);
      node.style('visibility', function(d) {
        return nodesId.includes(d.real_id.toString()) ? 'visible' : 'hidden';
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
