/*
global
alertify: false
call: false
capitalize: false
convertSelect: false
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

(function() {
  doc('https://enms.readthedocs.io/en/latest/workflows/index.html');
  convertSelect('#add_jobs', '#workflow-devices', '#workflow-pools');
  getWorkflowState();
})();

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
        data.subtype = edgeType;
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
let lastModified;

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
  graph.on('doubleClick', function(properties) {
    properties.event.preventDefault();
    const node = this.getNodeAt(properties.pointer.DOM);
    if (node) {
      const job = workflow.jobs.find((w) => w.id === node);
      if (job.type == 'Workflow') {
        switchToWorkflow(node);
      } else {
        editService(node);
      }
    }
  });
  $(`#add_jobs option[value='${wf.id}']`).remove();
  $('#add_jobs').selectpicker('refresh');
  lastModified = wf.last_modified;
  return graph;
}

/**
 * Display a workflow.
 * @param {workflowId} workflowId - Workflow ID.

 */
function switchToWorkflow(workflowId) {
  call(`/get/workflow/${workflowId}`, function(result) {
    workflow = result;
    graph = displayWorkflow(result);
    alertify.notify(`Workflow '${workflow.name}' displayed.`, 'success', 5);
  });
}

if (workflow) {
  $('#current-workflow').val(workflow.id);
  displayWorkflow(workflow);
} else {
  workflow = $('#current-workflow').val();
  if (workflow) {
    switchToWorkflow(workflow);
  } else {
    alertify.notify(`You must create a workflow in the
    'Workflow management' page first.`, 'error', 5);
  }
}

/**
 * Add an existing job to the workflow.
 */
function addJobToWorkflow() { // eslint-disable-line no-unused-vars
  if (!workflow) {
    alertify.notify(`You must create a workflow in the
    'Workflow management' page first.`, 'error', 5);
  } else {
    const url = `/automation/add_jobs_to_workflow/${workflow.id}`;
    fCall(url, '#add-job-form', function(jobs) {
      jobs.forEach((job) => {
        $('#add-job').modal('hide');
        if (graph.findNode(job.id).length == 0) {
          nodes.add(jobToNode(job));
        } else {
          alertify.notify(
            `Job '${job.name}' already in workflow.`, 'error', 5
          );
        }
      });
    });
  }
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
    label: capitalize(edge.subtype),
    type: edge.subtype,
    from: edge.source_id,
    to: edge.destination_id,
    smooth: {
      type: 'curvedCW',
      roundness:
        edge.subtype == 'success' ? 0.1 :
        edge.subtype == 'failure' ? -0.1 :
        0,
    },
    color: {
      color: edge.subtype == 'success' ? 'green'
      : edge.subtype == 'failure' ? 'red'
      : 'blue',
    },
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
  if (['success', 'failure', 'prerequisite'].includes(mode)) {
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
  $('#add_jobs').append(
    `<option value='${workflow.id}'>${workflow.name}</option>`
  );
  switchToWorkflow(this.value);
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
  'Logs': showLogs,
  'Edit Workflow': editWorkflow,
  'Workflow Logs': showWorkflowLogs,
  'Add Service or Workflow': partial(showModal, 'add-job'),
  'Delete': deleteSelection,
  'Create "Success" edge': partial(switchMode, 'success'),
  'Create "Failure" edge': partial(switchMode, 'failure'),
  'Create "Prerequisite" edge': partial(switchMode, 'prerequisite'),
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
 * Get Job State.
 * @param {id} id - Job Id.
 */
function getJobState(id) { // eslint-disable-line no-unused-vars
  call(`/get/service/${id}`, function(service) {
    if (service.status == 'Running') {
      colorJob(id, '#89CFF0');
      $('#status').text('Status: Running.');
      $('#current-job').text(`Current job: ${service.name}.`);
      setTimeout(partial(getJobState, id), 1500);
    } else {
      $('#status').text('Status: Idle.');
      $('#current-job').empty();
      colorJob(id, '#D2E5FF');
    }
  });
}

/**
 * Get Workflow State.
 */
function getWorkflowState() {
  if (workflow && workflow.id) {
    call(`/get/workflow/${workflow.id}`, function(wf) {
      if (wf.last_modified !== lastModified) {
        displayWorkflow(wf);
      }
      $('#status').text(`Status: ${wf.status}.`);
      if (wf.id == workflow.id) {
        if (Object.keys(wf.state).length !== 0) {
          if (wf.state.current_device) {
            $('#current-device').text(
              `Current device: ${wf.state.current_device}.`
            );
          }
          if (wf.state.current_job) {
            colorJob(wf.state.current_job.id, '#89CFF0');
            $('#current-job').text(
              `Current job: ${wf.state.current_job.name}.`
            );
          } else {
            $('#current-device,#current-job').empty();
          }
          if (wf.state.jobs) {
            $.each(wf.state.jobs, (id, success) => {
              colorJob(id, success ? '#32cd32' : '#FF6666');
            });
          }
        } else {
          $('#current-device,#current-job').empty();
          wf.jobs.forEach((job) => colorJob(job.id, '#D2E5FF'));
        }
        setTimeout(getWorkflowState, wf.status == 'Running' ? 700 : 15000);
      }
    });
  }
}

$(window).bind('beforeunload', function() {
  savePositions();
});
