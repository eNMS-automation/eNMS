/*
global
alertify: false
fields: false
users: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add user to datatable or edit line.
 * @param {mode} mode - Create or edit.
 * @param {properties} properties - Properties of the user.
 */
function addUser(mode, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showUserModal('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteUser('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

(function() {
  for (let i = 0; i < users.length; i++) {
    addUser('create', users[i]);
  }
})();

/**
 * Display user modal for creation.
 */
function showModal() { // eslint-disable-line no-unused-vars
  $('#edit-form').trigger('reset');
  $('#title').text('Create a New User');
  $('#edit').modal('show');
}

/**
 * Display user modal for editing.
 * @param {userId} userId - Id of the user to be deleted.
 */
function showUserModal(userId) { // eslint-disable-line no-unused-vars
  
  $.ajax({
    type: 'POST',
    url: `/admin/get/${userId}`,
    success: function(properties) {
      if (!properties) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      }
      for (const [property, value] of Object.entries(properties)) {
        $(`#${property}`).val(value);
      }
      $('#title').text(`Edit User '${properties.name}'`);
    },
  });
  $('#edit').modal('show');
}

/**
 * Create or edit user.
 */
function processData() { // eslint-disable-line no-unused-vars
  if ($('#edit-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: `/admin/process_user`,
      dataType: 'json',
      data: $('#edit-form').serialize(),
      success: function(user) {
        if (!user) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else {
          const title = $('#title').text().startsWith('Edit');
          const mode = title ? 'edit' : 'create';
          addUser(mode, user);
          const message = `User '${user.name}'
          ${mode == 'edit' ? 'edited' : 'created'}.`;
          alertify.notify(message, 'success', 5);
        }
      },
    });
    $('#edit').modal('hide');
  }
}

/**
 * Delete user.
 * @param {userId} userId - Id of the user to be deleted.
 */
function deleteUser(userId) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: `/admin/delete/${userId}`,
    success: function(user) {
      if (!user) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else {
        $(`#${userId}`).remove();
        alertify.notify(`User '${user.name}' deleted.`, 'error', 5);
      }
    },
  });
}
