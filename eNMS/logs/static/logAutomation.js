/*
global
alertify: false
call: false
fCall: false
fields: false
logRules: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add log rule to datatable or edit line.
 * @param {properties} properties - Properties of the log rule.
 * @param {mode} mode - Create or edit.
 */
function addLogRule(properties, mode) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }


  if (mode == 'edited') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

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
    addLogRule(logRules[i], 'create');
  }
})();


/**
 * Display log rule modal for editing.
 * @param {id} id - Id of the log rule.
 */
function showLogRuleModal(id) { // eslint-disable-line no-unused-vars
  call(`/get/logrule/${id}`, function(logRule) {
    for (const [property, value] of Object.entries(logRule)) {
      if (property.includes('regex')) {
        $(`#${property}`).prop('checked', value);
      } else {
        $(`#${property}`).val(value);
      }
      $('#jobs').val(logRule.jobs.map((j) => j.id));
      $('#title').text(`Edit log rule properties`);
    }
    $('#edit').modal('show');
  });
}


