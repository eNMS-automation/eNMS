/*
global
addInstance: false
convertSelect: false
logRules: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Add a service to the datatable.
 * @param {values} values - User properties.
 * @param {logrule} logrule - Log Rule.
 */
function tableActions(values, logrule) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('logrule', '${logrule.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteInstance('logrule', '${logrule.id}')">Delete</button>`
  );
}

(function() {
  convertSelect('#logrule-jobs');
  for (let i = 0; i < logRules.length; i++) {
    addInstance('create', 'logrule', logRules[i]);
  }
})();
