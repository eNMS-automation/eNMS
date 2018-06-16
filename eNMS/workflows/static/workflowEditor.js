var container = document.getElementById('network');
var dsoptions = {
  edges: {
    font: {
      size: 12
    }
  },
  nodes: {
    shape: 'box',
    font: {
      bold: {
        color: '#0077aa'
      }
    }
  },
  manipulation: {
    enabled: false,
    addNode: function (data, callback) {
      // filling in the popup DOM elements
      console.log(data);
    },
    editNode: function (data, callback) {
      // filling in the popup DOM elements
      console.log('edit', data);
    },
    addEdge: function (data, callback) {
      if (data.from != data.to) {
        data.type = edge_type;
        saveEdge(data);
        console.log('test');
        graph.addEdgeMode();
      }
    }
  }
};
var selectedNode = null;

function displayWorkflow(wf) {
  nodes = new vis.DataSet(wf.inner_tasks.map(taskToNode));
  edges = new vis.DataSet(wf.edges.map(edgeToEdge));
  data = {nodes: nodes, edges: edges};
  graph = new vis.Network(container, data, dsoptions);
  graph.setOptions( { physics: false } );
  graph.on('oncontext', function(properties) {
    properties.event.preventDefault()
    node = this.getNodeAt(properties.pointer.DOM);
    if(typeof node !== "undefined") {
      selectedNode = node;
    }
  });
  return graph;
}

if (workflow) {
  $("#workflow-name").val(workflow.id);
  displayWorkflow(workflow);
} else {
  $.ajax({
    type: "POST",
    url: `/workflows/get/${$("#workflow-name").val()}`,
    success: function(wf) {
      console.log(workflow);
      displayWorkflow(workflow);
      
    }
  });
}

function scheduleTask() {
  if (workflow && $("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: `/tasks/scheduler/inner_task/${workflow.id}`,
      dataType: "json",
      data: $("#scheduling-form").serialize(),
      success: function(result) {
        if (result === 'no node') {
          alertify.notify('No nodes selected.', 'error', 5);
        } else {
          $("#scheduling").modal('hide');
          nodes.add(taskToNode(result));
          saveNode(result);
        }
      }
    });
  } else {
    alertify.notify('Some fields are missing', 'error', 5);
  }
}


function saveNode(task) {
  $.ajax({
    type: "POST",
    url: `/workflows/add_node/${workflow.id}/${task.id}`,
    success: function(task) {
      alertify.notify("Task added to the workflow", 'success', 5);
    }
  });
}

function deleteNode(id) {
  $.ajax({
    type: "POST",
    url: `/workflows/delete_node/${workflow.id}/${id}`,
    success: function(task) {
      alertify.notify("Task delete from the workflow", 'success', 5);
    }
  });
}

function saveEdge(edge) {
  $.ajax({
    type: "POST",
    url: `/workflows/add_edge/${workflow.id}/${edge.type}/${edge.from}/${edge.to}`,
    success: function(edge) {
      alertify.notify("Edge added to the workflow", 'success', 5);
      edges.add(edgeToEdge(edge));
    }
  });
}

function deleteEdge(edgeId) {
  console.log(edgeId);
  $.ajax({
    type: "POST",
    url: `/workflows/delete_edge/${workflow.id}/${edgeId}`,
    success: function(edge) {
      alertify.notify("Edge deleted the workflow", 'success', 5);
    }
  });
}

function taskToNode(task) {
  return {
    id: task.id,
    label: task.name,
    type: task.type,
    x: task.x,
    y: task.y,
    color: task.id == workflow.start_task ? "green" : "#D2E5FF"
  };
}

function edgeToEdge(edge) {
  return {
    id: edge.id,
    label: edge.type,
    type: edge.type,
    from: edge.source.id,
    to: edge.destination.id,
    color: {color: edge.type == 'success' ? 'green' : 'red'},
    arrows: {to: {enabled: true}}
  };
}

function showModal(modal_name){
  $(`#${modal_name}`).modal('show');
}

function startScript() {
  start = nodes.get(graph.getSelectedNodes()[0]);
  console.log(start, start.id, start.length);
  if (start.length == 0 || !start.id) {
    alertify.notify("You must select a script first.", 'error', 5);
  } else {
    if (workflow.start_task) {
      console.log('test');
      nodes.update({id: workflow.start_task, color: "#D2E5FF"});
    }
    $.ajax({
      type: "POST",
      url: `/workflows/set_as_start/${workflow.id}/${start.id}`,
      success: function() {
        nodes.update({id: start.id, color: "green"});
        workflow.start_task = start.id
        alertify.notify("Start script updated", 'success', 5);
      }
    });
    alertify.notify(`Script ${start.label} set as start`, 'success', 5);
  }
}

// when a workflow is selected, apply it
$('#workflow').on('change', function() {
  $.ajax({
    type: "POST",
    url: `/workflows/get/${this.value}`,
    dataType: "json",
    success: function(workflow){
      var nodes = new vis.DataSet([]);
      for (var i = 0; i < workflow.tasks; i++) {
        var task = workflow[i];
        nodes.push({
          id: task.id,
          label: task.name,
        });
      }
      var data = {nodes: new vis.DataSet(nodes)};
      graph.setData(data);
    alertify.notify(`Workflow '${workflow.name}' displayed`, 'success', 5);
    }
  });
});

function deleteSelection() {
  graph.getSelectedNodes().map(node => deleteNode(node));
  graph.getSelectedEdges().map(edge => deleteEdge(edge));
  graph.deleteSelected();
  alertify.notify("Selected objects deleted", 'success', 5);
}

function switchMode(mode) {
  console.log(mode);
  if (mode == "success" || mode == "failure") {
    edge_type = mode;
    graph.addEdgeMode();
    alertify.notify(`Mode: creation of ${mode} edge`, 'success', 5);
  } else {
    graph.addNodeMode();
    alertify.notify("Mode: node motion", 'success', 5);
  }
}

function runWorkflow() {
  $.ajax({
    type: "POST",
    url: `/workflows/run_${workflow.id}`,
    contentType: 'application/json;charset=UTF-8',
    success: function(){
      alertify.notify("Workflow successfully started", 'success', 5);
    }
  });
}

function showTaskModal(id) {
  $.ajax({
    type: "POST",
    url: `/tasks/get/${id}`,
    success: function(task){
      console.log(task);
      for (var [property, value] of Object.entries(task)) {
        if ($(`#${property}`).length) {
          input = Array.isArray(value) ? value.map(s => s.id) : value
          console.log(input);
          $(`#${property}`).val(input);
        }
      }
    }
  });
  $('#scheduling').modal('show');
}

// when a filter is selected, apply it
$('#workflow-name').on('change', function() {

  $.ajax({
    type: "POST",
    url: `/workflows/get/${this.value}`,
    dataType: "json",
    success: function(wf) {
      workflow = wf;
      graph = displayWorkflow(wf)
      nodes.map(n => graph.moveNode(n.id, n.x, n.y));
    }
  });
});

function savePositions() {
  console.log(graph);
  $.ajax({
    type: "POST",
    url: "/workflows/save_positions",
    dataType: "json",
    contentType: 'application/json;charset=UTF-8',
    data: JSON.stringify(graph.getPositions(), null, '\t'),
    success: function() { }
  });
}

(function ($, window) {
  $.fn.contextMenu = function (settings) {
    return this.each(function () {
      // Open context menu
      $(this).on("contextmenu", function (e) {
        // return native menu if pressing control
        if (e.ctrlKey) return;
        //open menu
        var $menu = $(settings.menuSelector)
          .data("invokedOn", $(e.target))
          .show()
          .css({
            position: "absolute",
            left: getMenuPosition(e.clientX, 'width', 'scrollLeft'),
            top: getMenuPosition(e.clientY, 'height', 'scrollTop')
          })
          .off('click')
          .on('click', 'a', function (e) {
            $menu.hide();
            var $invokedOn = $menu.data("invokedOn");
            var $selectedMenu = $(e.target);
            settings.menuSelected.call(this, $invokedOn, $selectedMenu);
          });
        return false;
      });
      //make sure menu closes on any click
      $('body').click(function () {
        $(settings.menuSelector).hide();
      });
    });

    function getMenuPosition(mouse, direction, scrollDir) {
      var win = $(window)[direction](),
          scroll = $(window)[scrollDir](),
          menu = $(settings.menuSelector)[direction](),
          position = mouse + scroll;
      // opening menu would pass the side of the page
      if (mouse + menu > win && menu < mouse) 
        position -= menu;
        return position;
    }    
  };
})(jQuery, window);

var action = {
  'Edit': showTaskModal,
  'Logs': showTaskLogs,
  'Compare': compareTaskLogs
}

$("#network").contextMenu({
  menuSelector: "#contextMenu",
  menuSelected: function (invokedOn, selectedMenu) {
    var row = selectedMenu.text();
    action[row](selectedNode);
  }
});

$(window).bind('beforeunload', function() {
  savePositions()
});