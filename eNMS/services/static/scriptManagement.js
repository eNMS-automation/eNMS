/*
global
alertify: false
fields: false
types: false
scripts: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add a script to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {properties} properties - Properties of the script.
 */
function addScript(mode, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showScriptModal('${properties.type}',
    '${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showSchedulingModal('${properties.id}')">Schedule</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteScript('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

(function() {
  for (let i = 0; i < scripts.length; i++) {
    addScript('create', scripts[i]);
  }
})();

// replace the button value of all script forms with 'Update'
for (let i = 0; i < types.length; i++) {
  $(`#${types[i]}-button`).text('Update');
}

/**
 * Open scheduling modal for a script.
 * @param {id} id - Id of the script to schedule.
 */
function showSchedulingModal(id) { // eslint-disable-line no-unused-vars
  $('#job-div').hide();
  $('#job').val(id);
  $('#scheduling').modal('show');
}

/**
 * Create a new script.
 * @param {type} type - Type of script to create.
 */
function createScript(type) { // eslint-disable-line no-unused-vars
  if ($(`#${type}-form`).parsley().validate() ) {
    $.ajax({
      type: 'POST',
      url: `/scripts/create_script/${type}`,
      dataType: 'json',
      data: $(`#${type}-form`).serialize(),
      success: function() {
        alertify.notify('Script successfully updated.', 'success', 5);
      },
    });
    $(`#edit-${type}`).modal('hide');
  }
}

/**
 * Delete a script.
 * @param {id} id - Id of the script to delete.
 */
function deleteScript(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/scripts/delete/${id}`,
    success: function(scriptName) {
      table.row($(`#${id}`)).remove().draw(false);
      const message = `Script '${scriptName}' successfully deleted.`;
      alertify.notify(message, 'error', 5);
    },
  });
}
