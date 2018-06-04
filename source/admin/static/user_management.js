var table = $('#table').DataTable();

function addUser(mode, properties) {
  values = [];
  for (var i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs" onclick="showUserModal('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs" onclick="deleteUser('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    console.log(values)
    var rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr("id", `${properties.id}`);
  }
}

(function() {
  for (var i = 0; i < users.length; i++) {
    console.log(users[i]);
    addUser('create', users[i]);
  }
})();

function showModal() {
  $('#title').text('Add a new user');
  $('#edit').modal('show');
}

function showUserModal(name) {
  $('#title').text('Edit user properties');
  $.ajax({
    type: "POST",
    url: `/admin/get_${name}`,
    success: function(properties){
      for (const [property, value] of Object.entries(properties)) {
        $(`#${property}`).val(value);
      }
    }
  });
  $('#edit').modal('show');
}

function processData() {
  if ($('#edit-form').parsley().validate()) {
    $.ajax({
      type: "POST",
      url: `/admin/process_user`,
      dataType: "json",
      data: $('#edit-form').serialize(),
      success: function(user) {
        console.log(user)
        var mode = $('#title').text() == "Edit user properties" ? 'edit' : 'create'
        addUser(mode, user)
        message = `User ${user.name} ` + (mode == 'edit' ? 'edited !' : 'created !');
        alertify.notify(message, 'success', 5);
      }
    });
    $('#edit').modal('hide');
  }
}

function deleteUser(userId) {
  $(`#${userId}`).remove();
  $.ajax({
    type: "POST",
    url: `/admin/delete_${userId}`,
    success: function(userName) {
      alertify.notify(`User ${userName} deleted`, 'error', 5);
    }
  });
}