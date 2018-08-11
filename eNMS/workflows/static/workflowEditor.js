/* global alertify: false, vis: false */
/* global workflow: true, graph: true, nodes: true, edges: true */

const container = document.getElementById('network');
const dsoptions = {
  edges: {
    font: {
      size: 12,
    },
  },
  nodes: {
    shape: 'box',
    font: {
      bold: {
        color: '#0077aa',
      },
    },
  },
  manipulation: {
    enabled: false,
    addNode: function(data, callback) {
      // filling in the popup DOM elements
    },
    editNode: function(data, callback) {
      // filling in the popup DOM elements
    },
    addEdge: function(data, callback) {
      if (data.from != data.to) {
        data.type = edgeType;
        saveEdge(data);
        graph.addEdgeMode();
      }
    },
  },
};
let selectedNode = null;
let edgeType = 'success';

function displayWorkflow(wf) {
  nodes = new vis.DataSet(wf.tasks.map(taskToNode));
  edges = new vis.DataSet(wf.edges.map(edgeToEdge));
  graph = new vis.Network(container, {nodes: nodes, edges: edges}, dsoptions);
  graph.setOptions({physics: false});
  graph.on('oncontext', function(properties) {
    properties.event.preventDefault();
    node = this.getNodeAt(properties.pointer.DOM);
    if(typeof node !== 'undefined') {
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
  $('#workflow-name').val(workflow.id);
  displayWorkflow(workflow);
} else {
  $.ajax({
    type: 'POST',
    url: `/workflows/get/${$('#workflow-name').val()}`,
    success: function(wf) {
      workflow = wf;
      graph = displayWorkflow(wf);
      nodes.map(n => graph.moveNode(n.id, n.x, n.y));
    },
  });
}

function scheduleTask() {
  if (!workflow) {
    alertify.notify(`You must create a workflow in the
    'Workflow management' page first.`, 'error', 5); 
  }
  if ($('#scheduling-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: `/tasks/scheduler/${workflow.id}`,
      dataType: 'json',
      data: $('#scheduling-form').serialize(),
      success: function(result) {
        $('#scheduling').modal('hide');
        if (graph.findNode(result.id).length == 0) {
          nodes.add(taskToNode(result));
          saveNode(result);
          alertify.notify(`Task '${result.name}' created.`, 'success', 5);
        } else {
          alertify.notify(`Task '${result.name}' edited.`, 'success', 5);
        }
      },
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
  if ($('#add-existing-task').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: `/tasks/add_to_workflow/${workflow.id}`,
      dataType: 'json',
      data: $('#add-existing-task-form').serialize(),
      success: function(task) {
        $('#add-existing-task').modal('hide');
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
    type: 'POST',
    url: `/workflows/add_node/${workflow.id}/${task.id}`,
    success: function(task) {
      const message = `Task '${task.name}' added to the workflow.`;
      alertify.notify(message, 'success', 5);
    },
  });
}

function deleteNode(id) {
  $.ajax({
    type: 'POST',
    url: `/workflows/delete_node/${workflow.id}/${id}`,
    success: function(task) {
      const message = `Task '${task.name}' deleted from the workflow.`;
      alertify.notify(message, 'success', 5);
    },
  });
}

function saveEdge(edge) {
  const param = `${workflow.id}/${edge.type}/${edge.from}/${edge.to}`
  $.ajax({
    type: 'POST',
    url: `/workflows/add_edge/${param}`,
    success: function(edge) {
      alertify.notify('Edge added to the workflow', 'success', 5);
      edges.add(edgeToEdge(edge));
    },
  });
}

function deleteEdge(edgeId) {
  console.log(edgeId);
  $.ajax({
    type: 'POST',
    url: `/workflows/delete_edge/${workflow.id}/${edgeId}`,
    success: function(edge) {
      alertify.notify('Edge deleted the workflow', 'success', 5);
    },
  });
}

function taskToNode(task) {
  return {
    id: task.id,
    label: task.name,
    type: task.type,
    x: task.x,
    y: task.y,
    color: task.id == workflow.start_task ? 'green' : '#D2E5FF',
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
    arrows: {to: {enabled: true}},
  };
}

function showSchedulingModal(){
  $('#scheduling').modal('show');
}

function startScript() {
  let start = nodes.get(graph.getSelectedNodes()[0]);
  if (start.length == 0 || !start.id) {
    alertify.notify('You must select a script first.', 'error', 5);
  } else {
    if (workflow.start_task != 'None') {
      nodes.update({id: workflow.start_task, color: '#D2E5FF'});
    }
    $.ajax({
      type: 'POST',
      url: `/workflows/set_as_start/${workflow.id}/${start.id}`,
      success: function() {
        nodes.update({id: start.id, color: 'green'});
        workflow.start_task = start.id
        alertify.notify('Start script updated.', 'success', 5);
      },
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
  if (mode == 'success' || mode == 'failure') {
    edgeType = mode;
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
    type: 'POST',
    url: `/workflows/run_${workflow.id}`,
    contentType: 'application/json;charset=UTF-8',
    success: function() {
      alertify.notify('Workflow successfully started.', 'success', 5);
    },
  });
}

function showTaskModal(id) {
  $.ajax({
    type: 'POST',
    url: `/tasks/get/${id}`,
    success: function(task) {
      for (const [property, value] of Object.entries(task)) {
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
    type: 'POST',
    url: `/workflows/get/${this.value}`,
    dataType: 'json',
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
    type: 'POST',
    url: '/workflows/save_positions',
    dataType: 'json',
    contentType: 'application/json;charset=UTF-8',
    data: JSON.stringify(graph.getPositions(), null, '\t'),
    success: function() {
      // Positions saved
    },
  });
}

const action = {
  'Edit': showTaskModal,
  'Logs': showTaskLogs,
  'Compare': compareTaskLogs,
  'Set as start': startScript,
  'Add new task': showSchedulingModal,
  'Add existing task': partial(showModal, 'add-existing-task'),
  'Delete selection': deleteSelection,
  'Create success edge': partial(switchMode, 'success'),
  'Create failure edge': partial(switchMode, 'failure'),
  'Move nodes': partial(switchMode, 'node'),
}

$('.dropdown-submenu a.test').on('click', function(e) {
  $(this).next('ul').toggle();
  e.stopPropagation();
  e.preventDefault();
});

$('#network').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function (invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selectedNode);
  }
});

$(window).bind('beforeunload', function() {
  savePositions()
});