/*
global
addObjectToTable: false
nodes: false
fields: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

(function() {
  for (let i = 0; i < nodes.length; i++) {
    addObjectToTable('create', 'node', nodes[i]);
  }
})();

document.getElementById('file').onchange = function() {
  $('#form').submit();
};
