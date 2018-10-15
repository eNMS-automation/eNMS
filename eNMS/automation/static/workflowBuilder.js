/*
global
alertify: false
compareLogs: false
editService: false
partial: false
runJob: false
showLogs: false
showModal: false
vis: false
workflow: true
*/

const workflowBuilder = true; // eslint-disable-line no-unused-vars

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
  nodes = new vis.DataSet(wf.jobs.map(jobToNode));
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
    url: `/automation/get/${$('#workflow-name').val()}`,
    success: function(result) {
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        workflow = result;
        graph = displayWorkflow(result);
      }
    },
  });
}

/**
 * Add an existing job to the workflow.
 */
function runWorkflow() { // eslint-disable-line no-unused-vars
  runJob(workflow.id);
}

/**
 * Add an existing job to the workflow.
 */
function addJobToWorkflow() { // eslint-disable-line no-unused-vars
  if (!workflow) {
    alertify.notify(`You must create a workflow in the
    'Workflow management' page first.`, 'error', 5);
  }
  if ($('#add-job').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: `/automation/add_to_workflow/${workflow.id}`,
      dataType: 'json',
      data: $('#add-job-form').serialize(),
      success: function(job) {
        if (!job) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          $('#add-job').modal('hide');
          if (graph.findNode(job.id).length == 0) {
            nodes.add(jobToNode(job));
            saveNode(job);
            alertify.notify(`Job '${job.name}' created.`, 'success', 5);
          } else {
            alertify.notify(`Job already in workflow.`, 'error', 5);
          }
        }
      },
    });
  } else {
    alertify.notify('Some fields are missing.', 'error', 5);
  }
}


/**
 * Add job to the workflow object (back-end).
 * @param {job} job - job to add to the workflow.
 */
function saveNode(job) {
  $.ajax({
    type: 'POST',
    url: `/automation/add_node/${workflow.id}/${job.id}`,
    success: function(job) {
      if (!job) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        const message = `Job '${job.name}' added to the workflow.`;
        alertify.notify(message, 'success', 5);
      }
    },
  });
}

/**
 * Delete job from the workflow (back-end).
 * @param {id} id - Id of the job to be deleted.
 */
function deleteNode(id) {
  $.ajax({
    type: 'POST',
    url: `/automation/delete_node/${workflow.id}/${id}`,
    success: function(job) {
      if (!job) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        const message = `Job '${job.name}' deleted from the workflow.`;
        alertify.notify(message, 'success', 5);
      }
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
    url: `/automation/add_edge/${param}`,
    success: function(edge) {
      if (!edge) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        alertify.notify('Edge added to the workflow', 'success', 5);
        edges.add(edgeToEdge(edge));
      }
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
    url: `/automation/delete_edge/${workflow.id}/${edgeId}`,
    success: function(edge) {
      if (!edge) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        alertify.notify('Edge deleted the workflow', 'success', 5);
      }
    },
  });
}

/**
 * Convert job object to Vis job node.
 * @param {job} job - Job object.
 * @return {visJob}.
 */
function jobToNode(job) {
  let color;
  if (workflow.end_job) {
    color = job.id == workflow.start_job.id ? 'green' :
      job.id == workflow.end_job.id ? 'red' : '#D2E5FF';
  } else {
    color = '#D2E5FF';
  }
  return {
    id: job.id,
    label: job.name,
    type: job.type,
    x: job.positions[workflow.name] ? job.positions[workflow.name][0] : 0,
    y: job.positions[workflow.name] ? job.positions[workflow.name][1] : 0,
    color: color,
  };
}

/**
 * Convert edge object to Vis job edge.
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
 * Set a job as start of the workflow.
 */
function startJob() {
  let start = nodes.get(graph.getSelectedNodes()[0]);
  if (start.length == 0 || !start.id) {
    alertify.notify('You must select a job first.', 'error', 5);
  } else {
    if (workflow.start_job) {
      nodes.update({id: workflow.start_job.id, color: '#D2E5FF'});
    }
    $.ajax({
      type: 'POST',
      url: `/automation/set_as_start/${workflow.id}/${start.id}`,
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          nodes.update({id: start.id, color: 'green'});
          workflow.start_job = start;
        }
      },
    });
    alertify.notify(`Job ${start.label} set as start.`, 'success', 5);
  }
}

/**
 * Set a job as end of the workflow.
 */
function endJob() {
  let end = nodes.get(graph.getSelectedNodes()[0]);
  if (end.length == 0 || !end.id) {
    alertify.notify('You must select a job first.', 'error', 5);
  } else {
    if (workflow.end_job) {
      nodes.update({id: workflow.end_job.id, color: '#D2E5FF'});
    }
    $.ajax({
      type: 'POST',
      url: `/automation/set_as_end/${workflow.id}/${end.id}`,
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          nodes.update({id: end.id, color: 'red'});
          workflow.end_job = end;
        }
      },
    });
    alertify.notify(`Job ${end.label} set as end.`, 'success', 5);
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

$('#workflow-name').on('change', function() {
  savePositions();
  $.ajax({
    type: 'POST',
    url: `/automation/get/${this.value}`,
    dataType: 'json',
    success: function(result) {
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        workflow = result;
        graph = displayWorkflow(result);
        alertify.notify(`Workflow '${workflow.name}' displayed.`, 'success', 5);
      }
    },
  });
});

/**
 * Save positions of the workflow nodes.
 */
function savePositions() {
  $.ajax({
    type: 'POST',
    url: `/automation/save_positions/${workflow.id}`,
    dataType: 'json',
    contentType: 'application/json;charset=UTF-8',
    data: JSON.stringify(graph.getPositions(), null, '\t'),
    success: function(result) {
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      }
    },
  });
}

/**
 * Show workflow logs
 */
function showWorkflowLogs() {
  showLogs(workflow.id);
}

/**
 * Compare workflow logs
 */
function compareWorkflowLogs() {
  compareLogs(workflow.id);
}

const action = {
  'Run Workflow': runWorkflow,
  'Edit': editService,
  'Run': runJob,
  'Logs': showLogs,
  'Compare Logs': compareLogs,
  'Workflow Logs': showWorkflowLogs,
  'Compare Workflow Logs': compareWorkflowLogs,
  'Set as start': startJob,
  'Set as end': endJob,
  'Add Service or Workflow': partial(showModal, 'add-job'),
  'Delete': deleteSelection,
  'Create "Success" edge': partial(switchMode, 'success'),
  'Create "Failure" edge': partial(switchMode, 'failure'),
  'Move Nodes': partial(switchMode, 'node'),
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

function getWorkflowStatus(){
  $.ajax({
    type: 'POST',
    url: `/automation/get/${this.value}`,
    dataType: 'json',
    success: function(result) {
      if (!result) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        workflow = result;
        graph = displayWorkflow(result);
        alertify.notify(`Workflow '${workflow.name}' displayed.`, 'success', 5);
      }
    },
  });
  setTimeout(getWorkflowStatus, 2000);
}

getWorkflowStatus();

$(window).bind('beforeunload', function() {
  savePositions();
});
