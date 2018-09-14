/**
 * Open the script modal for editing.
 * @param {type} type - Type of script to create.
 * @param {id} id - Id of the script to edit.
 */
function showScriptModal(type, id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/scripts/get/${type}/${id}`,
    success: function(properties) {
      $('#title').text(`Edit ${properties.name} properties`);
      for (const [property, value] of Object.entries(properties)) {
        if (typeof(value) === 'boolean') {
          $(`#${type}-${property}`).prop('checked', value);
        } else {
          const gValue = property == 'payload' ? JSON.stringify(value) : value;
          $(`#${type}-${property}`).val(gValue);
        }
      }
    },
  });
  $(`#edit-${type}`).modal('show');
}
