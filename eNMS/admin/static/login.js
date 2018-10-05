/*
global
alertify: false
*/

/**
 * Create a new account.
 */
function signUp() { // eslint-disable-line no-unused-vars
  if ($('#create-user-form').parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: '/admin/create_new_user',
      dataType: 'json',
      data: $('#create-user-form').serialize(),
      success: function(result) {
        if (!result) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else if (result == 'duplicate') {
          const message = 'Cannot create new user: duplicate entry.';
          alertify.notify(message, 'error', 5);
        } else {
          alertify.notify('New user created.', 'success', 5);
          document.getElementById('login-button').click();
        }
      },
    });
  }
}
