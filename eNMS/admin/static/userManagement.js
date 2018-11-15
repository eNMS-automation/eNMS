/*
global
addInstance: false
convertSelect: false
doc: false
users: false
*/

const table = $('#table').DataTable(); // eslint-disable-line

/**
 * Edit a service.
 * @param {values} values - User properties.
 * @param {user} user - User.
 */
function tableActions(values, user) { // eslint-disable-line no-unused-vars
  values.push(
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('user', '${user.id}')">Edit</button>`,
    `<button type="button" class="btn btn-primary btn-xs"
    onclick="showTypeModal('user', '${user.id}', true)">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="confirmDeletion('user', '${user.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  convertSelect('#user-permissions');
  for (let i = 0; i < users.length; i++) {
    addInstance('create', 'user', users[i]);
  }
})();
