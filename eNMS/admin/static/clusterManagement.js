/*
global
addInstance: false
convertSelect: false
doc: false
clusters: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Edit a service.
 * @param {values} values - Cluster properties.
 * @param {cluster} cluster - Cluster.
 */
function tableActions(values, cluster) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('cluster', '${cluster.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('cluster', '${cluster.id}', true)">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="confirmDeletion('cluster', '${cluster.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  convertSelect('#cluster-permissions');
  for (let i = 0; i < clusters.length; i++) {
    addInstance('create', 'cluster', clusters[i]);
  }
})();
