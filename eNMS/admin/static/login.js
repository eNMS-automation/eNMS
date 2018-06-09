function signup() {
  if ($('#create-user-form').parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/admin/process_user",
      dataType: "json",
      data: $('#create-user-form').serialize(),
      success: function(result) {
        if (result == 'duplicate') {
          alertify.notify("Cannot create new user: duplicate entry", 'error', 5);
        } else {
          alertify.notify("New user created !", 'success', 5);
          document.getElementById('login-button').click();
        }
      }
    });
  };
}