/*
global
alertify: false
call: false
doc: false
fCall: false
fields: false
users: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

function tableActions(values, user) {
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('user', '${user.id}')">Edit</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTypeModal('user', '${user.id}', true)">Duplicate</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteInstance('user', '${user.id}')">Delete</button>`
  );
}

(function() {
  doc('https://enms.readthedocs.io/en/latest/security/access.html');
  for (let i = 0; i < users.length; i++) {
    addUser('create', users[i]);
  }
})();
