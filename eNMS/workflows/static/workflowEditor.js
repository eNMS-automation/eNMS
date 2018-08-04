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
  nodes = new vis.DataSet(wf.tasks.map(taskToNode));
  edges = new vis.DataSet(wf.edges.map(edgeToEdge));
  data = {nodes: nodes, edges: edges};
  graph = new vis.Network(container, data, dsoptions);
  graph.setOptions( { physics: false } );
  graph.on('oncontext', function(properties) {
    properties.event.preventDefault()
    node = this.getNodeAt(properties.pointer.DOM);
    if(typeof node !== "undefined") {
      $('.node-selection').show();
      $('.global').hide();
      selectedNode = node;
    } else {
      $('.global').show();
      $('.node-selection').hide();
    }
  });
  nodes.map(n => graph.moveNode(n.id, n.x, n.y));
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
      workflow = wf;
      graph = displayWorkflow(wf)
      nodes.map(n => graph.moveNode(n.id, n.x, n.y));
    }
  });
}

function scheduleTask() {
  if (!workflow) {
    alertify.notify(`You must create a workflow in the
    'Workflow management' page first.`, 'error', 5); 
  }
  if ($("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: `/tasks/scheduler/${workflow.id}`,
      dataType: "json",
      data: $('#scheduling-form').serialize(),
      success: function(result) {
        $("#scheduling").modal('hide');
        if (graph.findNode(result.id).length == 0) {
          nodes.add(taskToNode(result));
          saveNode(result);
          alertify.notify(`Task '${result.name}' created.`, 'success', 5);
        } else {
          alertify.notify(`Task '${result.name}' edited.`, 'success', 5);
        }
      }
    });
  } else {
    alertify.notify('Some fields are missing.', 'error', 5);
  }
}

function addTaskToWorkflow() {
  if (!workflow) {
    alertify.notify(`You must create a workflow in the
    'Workflow management' page first.`, 'error', 5); 
  }
  if ($("#add-existing-task").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: `/tasks/add_to_workflow/${workflow.id}`,
      dataType: "json",
      data: $('#add-existing-task-form').serialize(),
      success: function(task) {
        $("#add-existing-task").modal('hide');
        if (graph.findNode(task.id).length == 0) {
          nodes.add(taskToNode(task));
          saveNode(task);
          alertify.notify(`Task '${task.name}' created.`, 'success', 5);
        } else {
          alertify.notify(`Task already in workflow.`, 'error', 5);
        }
      }
    });
  } else {
    alertify.notify('Some fields are missing.', 'error', 5);
  }
}

function saveNode(task) {
  $.ajax({
    type: "POST",
    url: `/workflows/add_node/${workflow.id}/${task.id}`,
    success: function(task) {
      alertify.notify(`Task '${task.name}' added to the workflow.`, 'success', 5);
    }
  });
}

function deleteNode(id) {
  $.ajax({
    type: "POST",
    url: `/workflows/delete_node/${workflow.id}/${id}`,
    success: function(task) {
      alertify.notify(`Task '${task.name}' deleted from the workflow.`, 'success', 5);
    }
  });
}

function saveEdge(edge) {
  $.ajax({
    type: "POST",
    url: `/workflows/add_edge/${workflow.id}/${edge.type}/${edge.from}/${edge.to}`,
    success: function(edge) {
      alertify.notify('Edge added to the workflow', 'success', 5);
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
      alertify.notify('Edge deleted the workflow', 'success', 5);
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

function showSchedulingModal(){
  $('#scheduling').modal('show');
}

function startScript() {
  start = nodes.get(graph.getSelectedNodes()[0]);
  if (start.length == 0 || !start.id) {
    alertify.notify('You must select a script first.', 'error', 5);
  } else {
    if (workflow.start_task != 'None') {
      nodes.update({id: workflow.start_task, color: "#D2E5FF"});
    }
    $.ajax({
      type: "POST",
      url: `/workflows/set_as_start/${workflow.id}/${start.id}`,
      success: function() {
        nodes.update({id: start.id, color: "green"});
        workflow.start_task = start.id
        alertify.notify('Start script updated.', 'success', 5);
      }
    });
    alertify.notify(`Task ${start.label} set as start.`, 'success', 5);
  }
}

function deleteSelection() {
  graph.getSelectedNodes().map(node => deleteNode(node));
  graph.getSelectedEdges().map(edge => deleteEdge(edge));
  graph.deleteSelected();
}

function switchMode(mode) {
  if (mode == "success" || mode == "failure") {
    edge_type = mode;
    graph.addEdgeMode();
    alertify.notify(`Mode: creation of ${mode} edge.`, 'success', 5);
  } else {
    graph.addNodeMode();
    alertify.notify('Mode: node motion.', 'success', 5);
  }
  // close the bootstrap submenu for layers
  $('.dropdown-submenu a.test').next('ul').toggle();
}

function runWorkflow() {
  $.ajax({
    type: "POST",
    url: `/workflows/run_${workflow.id}`,
    contentType: 'application/json;charset=UTF-8',
    success: function(){
      alertify.notify('Workflow successfully started.', 'success', 5);
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
          $(`#${property}`).val(input);
        }
      }
    }
  });
  $('#scheduling').modal('show');
}

$('#workflow-name').on('change', function() {
  savePositions();
  $.ajax({
    type: "POST",
    url: `/workflows/get/${this.value}`,
    dataType: "json",
    success: function(wf) {
      workflow = wf;
      graph = displayWorkflow(wf);
      alertify.notify(`Workflow '${workflow.name}' displayed.`, 'success', 5);
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

function partial(func) {
  var args = Array.prototype.slice.call(arguments, 1);
  return function() {
    var allArguments = args.concat(Array.prototype.slice.call(arguments));
    return func.apply(this, allArguments);
  };
}

var action = {
  'Edit': showTaskModal,
  'Logs': showTaskLogs,
  'Compare': compareTaskLogs,
  'Set as start': startScript,
  'Add new task': showSchedulingModal,
  'Add existing task': partial(showModal, 'add-existing-task'),
  'Delete selection': deleteSelection,
  'Create success edge': partial(switchMode, 'success'),
  'Create failure edge': partial(switchMode, 'failure'),
  'Move nodes': partial(switchMode, 'node')
}

$('.dropdown-submenu a.test').on("click", function(e){
  $(this).next('ul').toggle();
  e.stopPropagation();
  e.preventDefault();
});

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