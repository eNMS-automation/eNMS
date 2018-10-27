/*
global
addObjectToTable: false
importTopology: false
links: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

(function() {
  $('#doc-link').attr(
    'href',
    'https://enms.readthedocs.io/en/latest/workflows/index.html'
  )
  for (let i = 0; i < links.length; i++) {
    addObjectToTable('create', 'link', links[i]);
  }
})();

document.getElementById('file').onchange = function() {
  importTopology('Link');
};
