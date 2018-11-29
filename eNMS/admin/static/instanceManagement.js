/*
global
addInstance: false
convertSelect: false
doc: false
instances: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Edit a service.
 * @param {values} values - Instance properties.
 * @param {instance} instance - Instance.
 */
function tableActions(values, instance) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('instance', '${instance.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('instance', '${instance.id}', true)">
    Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="confirmDeletion('instance', '${instance.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  convertSelect('#instance-permissions');
  for (let i = 0; i < instances.length; i++) {
    addInstance('create', 'instance', instances[i]);
  }
})();
