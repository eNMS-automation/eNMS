/*
global
addObjectToTable: false
devices: false
*/



(function() {
  for (let i = 0; i < devices.length; i++) {
    addObjectToTable('create', 'device', devices[i]);
  }
})();

document.getElementById('file').onchange = function() {
  importTopology('Device');
};