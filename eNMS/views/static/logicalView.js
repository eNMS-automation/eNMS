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

function linkToEdge(link) {
  return {
    from: link.source.id,
    to: link.destination.id,
  };
}

console.log(devices.map(deviceToNode))
var nodes = new vis.DataSet(devices.map(deviceToNode));
var edges = new vis.DataSet(links.map(linkToEdge));

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
var container = document.getElementById('logical_view');
var data = {
  nodes: nodes,
  edges: []
};
var options = {};
var network = new vis.Network(container, data, options);

// when a filter is selected, apply it
$('#select-filters').on('change', function() {
  call(`/inventory/pool_objects/${this.value}`, function(objects) {
    alertify.notify(`Filter applied.`, 'success', 5);
  });
});

(function() {
  doc('https://enms.readthedocs.io/en/latest/views/logical_view.html');
})();
