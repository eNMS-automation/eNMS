/*
global
alertify: false
call: false
doc: false
editService: false
fCall: false
partial: false
runJob: false
showLogs: false
showModal: false
showTypeModal: false
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
    },
    addEdge: function(data, callback) {
      if (data.from != data.to) {
        data.subtype = edgeType == 'success' ? true : false;
        saveEdge(data);
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
    const edge = this.getEdgeAt(properties.pointer.DOM);
    if (typeof node !== 'undefined' && node != 1 && node != 2) {
      graph.selectNodes([node]);
      $('.global,.edge-selection').hide();
      $('.node-selection').show();
      selectedNode = node;
    } else if (typeof edge !== 'undefined' && node != 1 && node != 2) {
      graph.selectEdges([edge]);
      $('.global,.node-selection').hide();
      $('.edge-selection').show();
      selectedNode = node;
    } else {
      $('.node-selection').hide();
      $('.global').show();
    }
  });
  return graph;
}

if (workflow) {
  $('#current-workflow').val(workflow.id);
  displayWorkflow(workflow);
} else {
  call(`/get/workflow/${$('#current-workflow').val()}`, function(result) {
    workflow = result;
    graph = displayWorkflow(result);
  });
}

/**
 * Add an existing job to the workflow.
 */
function addJobToWorkflow() { // eslint-disable-line no-unused-vars
  if (!workflow) {
    alertify.notify(`You must create a workflow in the
    'Workflow management' page first.`, 'error', 5);
  } else {
    const url = `/automation/add_to_workflow/${workflow.id}`;
    fCall(url, '#add-job-form', function(job) {
      $('#add-job').modal('hide');
      if (graph.findNode(job.id).length == 0) {
        nodes.add(jobToNode(job));
        saveNode(job);
        alertify.notify(`Job '${job.name}' created.`, 'success', 5);
      } else {
        alertify.notify(`Job already in workflow.`, 'error', 5);
      }
    });
  }
}

/**
 * Add job to the workflow object (back-end).
 * @param {job} job - job to add to the workflow.
 */
function saveNode(job) {
  call(`/automation/add_node/${workflow.id}/${job.id}`, function(job) {
    alertify.notify(`'${job.name}' added to the workflow.`, 'success', 5);
  });
}

/**
 * Delete job from the workflow (back-end).
 * @param {id} id - Id of the job to be deleted.
 */
function deleteNode(id) {
  call(`/automation/delete_node/${workflow.id}/${id}`, function(job) {
    alertify.notify(`'${job.name}' deleted from the workflow.`, 'success', 5);
  });
}

/**
 * Add edge to the workflow object (back-end).
 * @param {edge} edge - Edge to add to the workflow.
 */
function saveEdge(edge) {
  const param = `${workflow.id}/${edge.subtype}/${edge.from}/${edge.to}`;
  call(`/automation/add_edge/${param}`, function(edge) {
    edges.add(edgeToEdge(edge));
    graph.addEdgeMode();
  });
}

/**
 * Delete edge from the workflow (back-end).
 * @param {edgeId} edgeId - Id of the edge to be deleted.
 */
function deleteEdge(edgeId) {
  call(`/automation/delete_edge/${workflow.id}/${edgeId}`, () => {});
}

/**
 * Convert job object to Vis job node.
 * @param {job} job - Job object.
 * @return {visJob}.
 */
function jobToNode(job) {
  let color;
  if (job.name == 'Start' || job.name == 'End') {
    color = 'pink';
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
    label: edge.subtype ? 'Success' : 'Failure',
    type: edge.subtype,
    from: edge.source_id,
    to: edge.destination_id,
    color: {color: edge.subtype ? 'green' : 'red'},
    arrows: {to: {enabled: true}},
  };
}

/**
 * Delete selected nodes and edges.
 */
function deleteSelection() {
  const node = graph.getSelectedNodes()[0];
  if (node != 1 && node != 2) {
    if (node) {
      deleteNode(node);
    }
    graph.getSelectedEdges().map((edge) => deleteEdge(edge));
    graph.deleteSelected();
  } else {
    alertify.notify('Start and End cannot be deleted', 'error', 5);
  }
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
  $('.dropdown-submenu a.menu-layer').next('ul').toggle();
}

$('#current-workflow').on('change', function() {
  savePositions();
  call(`/get/workflow/${this.value}`, function(result) {
    workflow = result;
    graph = displayWorkflow(result);
    alertify.notify(`Workflow '${workflow.name}' displayed.`, 'success', 5);
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
 * Edit Workflow
 */
function editWorkflow() {
  showTypeModal('workflow', workflow.id);
}

const action = {
  'Run Workflow': runWorkflow,
  'Edit': editService,
  'Run': runJob,
  'Service Logs': showLogs,
  'Edit Workflow': editWorkflow,
  'Workflow Logs': showWorkflowLogs,
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

/**
 * Start the workflow.
 */
function runWorkflow() { // eslint-disable-line no-unused-vars
  workflow.jobs.forEach((job) => colorJob(job.id, '#D2E5FF'));
  runJob(workflow.id);
}

/**
 * Get Workflow State.
 * @param {id} id - Workflow Id.
 * @param {color} color - Node color.
 */
function colorJob(id, color) {
  if (id != 1 && id != 2) {
    nodes.update({id: id, color: color});
  }
}

/**
 * Get Workflow State.
 */
function getWorkflowState() {
  if (workflow) {
    call(`/get/workflow/${workflow.id}`, function(wf) {
      $('#status').text(`Status: ${wf.status}.`);
      if (Object.keys(wf.state).length !== 0) {
        if (wf.state.current_device) {
          $('#current-device').text(
            `Current device: ${wf.state.current_device}.`
          );
        }
        if (wf.state.current_job) {
          colorJob(wf.state.current_job.id, '#89CFF0');
          $('#current-job').text(`Current job: ${wf.state.current_job.name}.`);
        } else {
          $('#current-device,#current-job').empty();
        }
        if (wf.state.jobs) {
          $.each(wf.state.jobs, (id, success) => {
            colorJob(id, success ? '#32cd32' : '#FF6666');
          });
        }
      } else {
        $('#current-job').text('');
        wf.jobs.forEach((job) => colorJob(job.id, '#D2E5FF'));
      }
    });
  }
  setTimeout(getWorkflowState, 1000);
}

$(window).bind('beforeunload', function() {
  savePositions();
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/workflows/index.html');
  getWorkflowState();
})();
