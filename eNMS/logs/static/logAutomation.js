/*
global
alertify: false
call: false
fCall: false
fields: false
logRules: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Add a service to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {properties} properties - Properties of the service.
 */
function tableActions(values, logrule) {
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('logrule', '${logrule.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteInstance('logrule', '${logrule.id}')">Delete</button>`
  );
}

(function() {
  for (let i = 0; i < logRules.length; i++) {
    addInstance('create', 'logrule', logRules[i]);
  }
})();
