/*
global
addObjectToTable: false
alertify: false
linkTable: false
nodeTable: false
*/

/**
 * Display object modal for editing.
 * @param {type} type - Node or link.
 * @param {id} id - Id of the object to edit.
 */
function showObjectModal(type, id) { // eslint-disable-line no-unused-vars
  $('#title').text(`Edit ${type} properties`);
  $.ajax({
    type: 'POST',
    url: `/objects/get/${type}/${id}`,
    success: function(properties) {
      for (const [property, value] of Object.entries(properties)) {
        $(`#${type}-${property}`).val(value);
      }
    },
  });
  if (type == 'node') {
    $.ajax({
      type: 'POST',
      url: `/views/get_logs_${id}`,
      success: function(logs) {
        $('#logs').text(logs);
      },
    });
  }
  $(`#edit-${type}`).modal('show');
}

/**
 * Edit object.
 * @param {type} type - Node or link.
 */
function editObject(type) { // eslint-disable-line no-unused-vars
  if ($(`#edit-${type}-form`).parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/objects/edit_object',
      dataType: 'json',
      data: $(`#edit-${type}-form`).serialize(),
      success: function(properties) {
        const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
        // the object can be edited from the views,
        // in which case we don't need to add it to the table
        if (typeof nodeTable !== 'undefined') {
          addObjectToTable(mode, type, properties);
        }
        const message = `Object ${properties.name}
        ${mode == 'edit' ? 'edited' : 'created'}.`;
        alertify.notify(message, 'success', 5);
      },
    });
    $(`#edit-${type}`).modal('hide');
  }
}

/**
 * Delete object.
 * @param {type} type - Node or link.
 * @param {id} id - Id of the object to delete.
 */
function deleteObject(type, id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/objects/delete/${type}/${id}`,
    success: function(properties) {
      const table = type == 'node' ? nodeTable : linkTable;
      table.row($(`#${type}-${id}`)).remove().draw(false);
      alertify.notify(
        `Object '${properties.name}' successfully deleted.`,
        'error', 5
    );
    },
  });
}
