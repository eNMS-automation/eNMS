/*
global
addObjectToTable: false
links: false
fields: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

(function() {
  for (let i = 0; i < links.length; i++) {
    addObjectToTable('create', 'link', links[i]);
  }
})();

document.getElementById('file').onchange = function() {
  $('#form').submit();
};
