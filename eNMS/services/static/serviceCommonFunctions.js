/**
 * Open the service modal for editing.
 * @param {type} type - Type of service to create.
 * @param {id} id - Id of the service to edit.
 */
function showServiceModal(type, id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/services/get/${type}/${id}`,
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
