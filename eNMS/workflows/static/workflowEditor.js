/*
global
alertify: false
compareTaskLogs: false
partial: false
showTaskLogs: false
vis: false
workflow: true
*/

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
        data.type = edgeType == 'success' ? true : false;
        saveEdge(data);
        graph.addEdgeMode();
      }
    },
  },
};

let nodes;
let edges;
let graph;
let selectedNode;
let edgeType;

/**
 * Display a workflow.
 * @param {wf} wf - A workflow.
 * @return {graph}
 */
function displayWorkflow(wf) {
  nodes = new vis.DataSet(wf.tasks.map(taskToNode));
  edges = new vis.DataSet(wf.edges.map(edgeToEdge));
  graph = new vis.Network(container, {nodes: nodes, edges: edges}, dsoptions);
  graph.setOptions({physics: false});
  graph.on('oncontext', function(properties) {
    properties.event.preventDefault();
    const node = this.getNodeAt(properties.pointer.DOM);
    if (typeof node !== 'undefined') {
      $('.node-selection').show();
      $('.global').hide();
      selectedNode = node;
    } else {
      $('.global').show();
      $('.node-selection').hide();
    }
  });
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
    },
  });
}

/**
 * Schedule a task.
 */
function scheduleTask() { // eslint-disable-line no-unused-vars
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

/**
 * Add an existing task to the workflow.
 */
function addTaskToWorkflow() { // eslint-disable-line no-unused-vars
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
      },
    });
  } else {
    alertify.notify('Some fields are missing.', 'error', 5);
  }
}

/**
 * Add task to the workflow object (back-end).
 * @param {task} task - Task to add to the workflow.
 */
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

/**
 * Delete task from the workflow (back-end).
 * @param {id} id - Id of the task to be deleted.
 */
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

/**
 * Add edge to the workflow object (back-end).
 * @param {edge} edge - Edge to add to the workflow.
 */
function saveEdge(edge) {
  const param = `${workflow.id}/${edge.type}/${edge.from}/${edge.to}`;
  $.ajax({
    type: 'POST',
    url: `/workflows/add_edge/${param}`,
    success: function(edge) {
      alertify.notify('Edge added to the workflow', 'success', 5);
      edges.add(edgeToEdge(edge));
    },
  });
}

/**
 * Delete edge from the workflow (back-end).
 * @param {edgeId} edgeId - Id of the edge to be deleted.
 */
function deleteEdge(edgeId) {
  $.ajax({
    type: 'POST',
    url: `/workflows/delete_edge/${workflow.id}/${edgeId}`,
    success: function(edge) {
      alertify.notify('Edge deleted the workflow', 'success', 5);
    },
  });
}

/**
 * Convert task object to Vis task node.
 * @param {task} task - Task object.
 * @return {visTask}.
 */
function taskToNode(task) {
  return {
    id: task.id,
    label: task.name,
    type: task.type,
    x: task.positions[workflow.name] ? task.positions[workflow.name][0] : 0,
    y: task.positions[workflow.name] ? task.positions[workflow.name][1] : 0,
    color: task.id == workflow.start_task ? 'green' :
      task.id == workflow.end_task ? 'red' : '#D2E5FF',
  };
}

/**
 * Convert edge object to Vis task edge.
 * @param {edge} edge - Edge object.
 * @return {visEdge}.
 */
function edgeToEdge(edge) {
  return {
    id: edge.id,
    label: edge.type ? 'Success' : 'Failure',
    type: edge.type,
    from: edge.source.id,
    to: edge.destination.id,
    color: {color: edge.type ? 'green' : 'red'},
    arrows: {to: {enabled: true}},
  };
}

/**
 * Show scheduling modal.
 */
function showSchedulingModal() {
  $('#scheduling').modal('show');
  $('.dropdown-submenu a.menu-task').next('ul').toggle();
}

/**
 * Display modal to add an existing task.
 */
function showExistingTaskModal() {
  $('#add-existing-task').modal('show');
  $('.dropdown-submenu a.menu-task').next('ul').toggle();
}

/**
 * Set a task as start of the workflow.
 */
function startTask() {
  let start = nodes.get(graph.getSelectedNodes()[0]);
  if (start.length == 0 || !start.id) {
    alertify.notify('You must select a task first.', 'error', 5);
  } else {
    if (workflow.start_task != 'None') {
      nodes.update({id: workflow.start_task, color: '#D2E5FF'});
    }
    $.ajax({
      type: 'POST',
      url: `/workflows/set_as_start/${workflow.id}/${start.id}`,
      success: function() {
        nodes.update({id: start.id, color: 'green'});
        workflow.start_task = start.id;
      },
    });
    alertify.notify(`Task ${start.label} set as start.`, 'success', 5);
  }
}

/**
 * Set a task as end of the workflow.
 */
function endTask() {
  let end = nodes.get(graph.getSelectedNodes()[0]);
  if (end.length == 0 || !end.id) {
    alertify.notify('You must select a task first.', 'error', 5);
  } else {
    if (workflow.end_task != 'None') {
      nodes.update({id: workflow.end_task, color: '#D2E5FF'});
    }
    $.ajax({
      type: 'POST',
      url: `/workflows/set_as_end/${workflow.id}/${end.id}`,
      success: function() {
        nodes.update({id: end.id, color: 'red'});
        workflow.end_task = end.id;
      },
    });
    alertify.notify(`Task ${end.label} set as end.`, 'success', 5);
  }
}

/**
 * Delete selected nodes and edges.
 */
function deleteSelection() {
  graph.getSelectedNodes().map((node) => deleteNode(node));
  graph.getSelectedEdges().map((edge) => deleteEdge(edge));
  graph.deleteSelected();
}

/**
 * Change the mode (motion, creation of success or failure edge).
 * @param {mode} mode - Mode to switch to.
 */
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
  $('.dropdown-submenu a.menu-layer').next('ul').toggle();
}

/**
 * Show task modal for editing.
 * @param {id} id - Id of the task to edit.
 */
function showTaskModal(id) {
  $.ajax({
    type: 'POST',
    url: `/tasks/get/${id}`,
    success: function(task) {
      for (const [property, value] of Object.entries(task)) {
        if ($(`#${property}`).length) {
          const input = Array.isArray(value) ? value.map((s) => s.id) : value;
          $(`#${property}`).val(input);
        }
      }
    },
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
    },
  });
});

/**
 * Save positions of the workflow nodes.
 */
function savePositions() {
  $.ajax({
    type: 'POST',
    url: `/workflows/save_positions/${workflow.id}`,
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
  'Set as start': startTask,
  'Set as end': endTask,
  'Add new task': showSchedulingModal,
  'Add existing task': showExistingTaskModal,
  'Delete selection': deleteSelection,
  'Create success edge': partial(switchMode, 'success'),
  'Create failure edge': partial(switchMode, 'failure'),
  'Move nodes': partial(switchMode, 'node'),
};

$('.dropdown-submenu a.menu-submenu').on('click', function(e) {
  $(this).next('ul').toggle();
  e.stopPropagation();
  e.preventDefault();
});

$('#network').contextMenu({
  menuSelector: '#contextMenu',
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selectedNode);
  },
});

$(window).bind('beforeunload', function() {
  savePositions();
});
