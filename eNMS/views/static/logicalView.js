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
let visDevices = [];
let selectedDevices = [];

function deviceToNode(device) {
  return {
    id: device.id,
    label: device.name,
    image: `static/images/default/${device.subtype}.gif`,
    shape: 'image'
  };
}

var nodes = new vis.DataSet(map(deviceToNode, devices));

/*
// create an array with edges
var edges = new vis.DataSet([
{% for link, properties in link_table.items() %}  
    { 
    from: {{ link['source']['id'] }}, 
    to: {{ link['destination']['id'] }}, 
    label: '{{ link[labels['link']] }}',
    color: {color: '{{ link.color }}'},
    },
{% endfor %}
]);
/*
// create a network
var container = document.getElementById('mynetwork');
var data = {
  nodes: nodes,
  //edges: edges
};
var options = {};
var network = new vis.Network(container, data, options);

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

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    alertify.notify(`Filter applied.`, 'success', 5);
  });
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/logical_view.html');
})();
