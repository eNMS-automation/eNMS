var selected_nodes = [];

function sendSelection() {
  $("#nodes").val(selected_nodes.map(s => s[1].real_id));
}

// selection function
function selectNode(d) {
  // we stop the propagation up the DOM tree so that the 
  // unselectAll event bound to the canvas is not triggered
  d3.event.stopPropagation();
  // add both the HTML and graph elements in the selected_nodes array
  selected_nodes.push([this, d]);
  d3.select(this)
    .select('image')
    .attr("xlink:href", d.selected_img);
  sendSelection();
};

// selection function
function showNodeProperties(d) {
  showObjectModal('node', d.real_id);
};

function showLinkProperties(d) {
  showObjectModal('link', d.real_id);
};

function unselectAll() {
  d3.event.preventDefault();
  for (var i = 0; i < selected_nodes.length; i++) {
    d3.select(selected_nodes[i][0])
      .select('image')
      .attr("xlink:href", selected_nodes[i][1].img);
  }
  selected_nodes = [];
  sendSelection();
};

var div = d3.select("body").append("div")	
  .attr("class", "tooltip")				

var width = 960,
    height = 500

var zoom = d3.behavior.zoom()
  .scaleExtent([1, 50])
  .on("zoom", zoomed);

var svg = d3.select("#logical_view").append("svg")
  .attr("width", width)
  .attr("height", height)
  .on("click", unselectAll)
  .call(zoom)
  .on("mousedown.zoom", null);


function rect(x, y, w, h) {
  return "M"+[x,y]+" l"+[w,0]+" l"+[0,h]+" l"+[-w,0]+"z";
}

var selection = svg.append("path")
  .attr("class", "selection")
  .attr("visibility", "hidden");

var startSelection = function(start) {
  selection.attr("d", rect(start[0], start[0], 0, 0))
    .attr("visibility", "visible");
};

var moveSelection = function(start, moved) {
  selection.attr("d", rect(
    start[0],
    start[1],
    moved[0] - start[0],
    moved[1] - start[1]
  ));
};

var endSelection = function(start, end) {
    var min_x = Math.min(start[0], end[0]);
        max_x = Math.max(start[0], end[0]);
        min_y = Math.min(start[1], end[1]);
        max_y = Math.max(start[1], end[1]);
    console.log(start, end, min_x, max_x, min_y, max_y);
  selection.attr("visibility", "hidden");
  // select all nodes in the rectangle
  d3.selectAll('.node')  //here's how you get all the nodes
    .each(function(d) {                    
      if (min_x <= d.x && d.x <= max_x && min_y <= d.y && d.y <= max_y) {
        selected_nodes.push([this, d]);
        d3.select(this)
          .select('image')
          .attr("xlink:href", d.selected_img);
      }
    });
  sendSelection();
};

svg.on("mousedown", function() {
  // same binding as leaflet: shift + left-click button for selection
  if (!d3.event.shiftKey || ((d3.event.which !== 1) && (d3.event.button !== 1))) {
    return false;
  }
  
  var subject = d3.select(window);
      parent = this.parentNode;
      start = d3.mouse(parent);
  startSelection(start);
  subject
    .on("mousemove.selection", function() {
      moveSelection(start, d3.mouse(parent));
    })
    .on("mouseup.selection", function() {
      endSelection(start, d3.mouse(parent));
      subject
        .on("mousemove.selection", null)
        .on("mouseup.selection", null);
    });
});

svg.on("touchstart", function() {
  var subject = d3.select(this);
      parent = this.parentNode;
      id = d3.event.changedTouches[0].identifier;
      start = d3.touch(parent, id)
      pos;
    startSelection(start);
    subject
      .on("touchmove."+id, function() {
        if (pos = d3.touch(parent, id)) {
          moveSelection(start, pos);
        }
      })
      .on("touchend."+id, function() {
        if (pos = d3.touch(parent, id)) {
          endSelection(start, pos);
          subject
            .on("touchmove."+id, null)
            .on("touchend."+id, null);
        }
      });
});

var force = d3.layout.force()
  .gravity(0.2)
  .distance(10)
  .charge(-100)
  .size([width, height]);

force
  .nodes(graph.nodes)
  .links(graph.links)
  .start();

var container = svg.append("g");

var link = container.selectAll(".link")
  .data(graph.links)
  .enter().append("line")
  .attr("class", "link")
  .on("dblclick", showLinkProperties);

var node = container.selectAll(".node")
  .data(graph.nodes)
  .enter().append("g")
  .attr("class", "node")
  .call(force.drag)
  .on("click", selectNode)
  .on("dblclick", showNodeProperties);

function zoomed() {
  container.attr(
    "transform",
    "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")"
  );
}

var images = node.append("image")
  .attr("xlink:href", function(d) { return d.img; })
  .attr("x", -8)
  .attr("y", -8)
  .attr("width", 16)
  .attr("height", 16)

var label = node.append("text")
  .attr("dx", 8)
  .attr("dy", ".35em")
  .text(function(d) { return d.name });

force.on("tick", function() {
  link
    .attr("x1", function(d) { return d.source.x; })
    .attr("y1", function(d) { return d.source.y; })
    .attr("x2", function(d) { return d.target.x; })
    .attr("y2", function(d) { return d.target.y; });
  node.attr("transform", function(d) {
    return "translate(" + d.x + "," + d.y + ")";
  });
});

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
    console.log(this.value);
  $.ajax({
    type: "POST",
    url: `/objects/pool_objects/${this.value}`,
    dataType: "json",
    success: function(objects){
      var nodes_id = objects.nodes.map(n => n.id);
      var links_id = objects.links.map(l => l.id);
      node.style("visibility", function(d) {      
        return nodes_id.includes(d.real_id.toString()) ? "visible" : "hidden";
      });
      link.style("visibility", function(d) {  
        return links_id.includes(d.real_id.toString()) ? "visible" : "hidden";
      });
      alertify.notify(`Filter applied.`, 'success', 5);
    }
  });
});

var action = {
  'Parameters': partial(showModal, 'filters'),
  'Add new task': partial(showModal, 'scheduling'),
}

$("#logical_view").contextMenu({
  menuSelector: "#contextMenu",
  menuSelected: function (invokedOn, selectedMenu) {
    var row = selectedMenu.text();
    action[row]();
  }
});