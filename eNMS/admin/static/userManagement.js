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
  $('#title').text('Add a new user');
  $('#edit').modal('show');
}

/**
 * Display user modal for editing.
 * @param {name} name - Name of the user to be deleted.
 */
function showUserModal(name) { // eslint-disable-line no-unused-vars
  $('#title').text('Edit user properties');
  $.ajax({
    type: 'POST',
    url: `/admin/get_${name}`,
    success: function(properties) {
      for (const [property, value] of Object.entries(properties)) {
        $(`#${property}`).val(value);
      }
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
        const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'create';
        addUser(mode, user);
        const message = `User '${user.name}'
        ${mode == 'edit' ? 'edited' : 'created'}.`;
        alertify.notify(message, 'success', 5);
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
  $(`#${userId}`).remove();
  $.ajax({
    type: 'POST',
    url: `/admin/delete_${userId}`,
    success: function(userName) {
      alertify.notify(`User '${userName}' deleted.`, 'error', 5);
    },
  });
}
