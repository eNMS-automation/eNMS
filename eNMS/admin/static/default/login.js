/*
global
alertify: false
fCall: false
*/

/**
 * Create a new account.
 */
function signUp() { // eslint-disable-line no-unused-vars
  fCall('/admin/create_new_user', '#create-user-form', function(result) {
    if (result == 'duplicate') {
      alertify.notify('Cannot create new user: duplicate entry.', 'error', 5);
    } else {
      alertify.notify('New user created.', 'success', 5);
      document.getElementById('login-button').click();
    }
  });
}
