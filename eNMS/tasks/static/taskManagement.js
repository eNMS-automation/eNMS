/*
global
fields: false
tasks: false
*/

const table = $('#table').DataTable(); // eslint-disable-line new-cap

/**
 * Add a task to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {properties} properties - Properties of the task to add.
 */
function addTask(mode, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    if (fields[i] != 'recurrent') {
      values.push(`${properties[fields[i]]}`);
    }
  }
  const status = properties.status == 'active' ? 'pause' : 'resume';
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showTaskLogs('${properties.id}')"></i>Logs</a></button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="compareTaskLogs('${properties.id}')"></i>Compare</a></button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="showTaskModal('${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-success btn-xs"
    onclick="runTask('${properties.id}')">Run</button>`,
    `<button id="pause-resume-${properties.id}" type="button"
    class="btn btn-danger btn-xs" onclick="${status}Task('${properties.id}')">
    ${status.charAt(0).toUpperCase() + status.substr(1)}</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteTask('${properties.id}')">Delete</button>`
  );

  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

(function() {
  if (typeof tasks !== 'undefined') {
    for (let i = 0; i < tasks.length; i++) {
      addTask('create', tasks[i]);
    }
  }
})();
