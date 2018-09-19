/*
global
alertify: false
fields: false
services: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add a service to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {properties} properties - Properties of the service.
 */
function addService(mode, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showSchedulingModal('${properties.id}')">Schedule</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteService('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

(function() {
  for (let i = 0; i < services.length; i++) {
    addService('create', services[i]);
  }
})();

/**
 * Open scheduling modal for a service.
 * @param {id} id - Id of the service to schedule.
 */
function showSchedulingModal(id) { // eslint-disable-line no-unused-vars
  $('#job-div').hide();
  $('#job').val(id);
  $('#scheduling').modal('show');
}

/**
 * Create a new service.
 * @param {type} type - Type of service to create.
 */
function createService(type) { // eslint-disable-line no-unused-vars
  if ($(`#${type}-form`).parsley().validate() ) {
    $.ajax({
      type: 'POST',
      url: `/services/create_service/${type}`,
      dataType: 'json',
      data: $(`#${type}-form`).serialize(),
      success: function() {
        alertify.notify('Service successfully updated.', 'success', 5);
      },
    });
    $(`#edit-${type}`).modal('hide');
  }
}

/**
 * Delete a service.
 * @param {id} id - Id of the service to delete.
 */
function deleteService(id) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/services/delete/${id}`,
    success: function(serviceName) {
      table.row($(`#${id}`)).remove().draw(false);
      const message = `Service '${serviceName}' successfully deleted.`;
      alertify.notify(message, 'error', 5);
    },
  });
}
