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
let selectedDevices = [];

var nodes = new vis.DataSet([
{% for node, properties in node_table.items() %}  
    {
    id: {{ node.id }}, 
    label: '{{ node[labels['node']] }}', 
    image: 'static/images/default/{{ node.subtype }}.gif', 
    shape: 'image', 
    title: "{% for property in properties %}\
    <b>{{names[property]}}</b>: {{ node[property] }}<br>{% endfor %}"
    },
{% endfor %}
]);

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

// create a network
var container = document.getElementById('mynetwork');
var data = {
  nodes: nodes,
  edges: edges
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
