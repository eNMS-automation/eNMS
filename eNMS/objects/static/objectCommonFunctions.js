/*
global
alertify: false
call: false
capitalize: false
fCall: false
fields: false
partial: false
table: false
*/

/**
 * Flip Combo box depending on whether or not authentication is selected.
 */
function flipAuthenticationCombo() {
  $('#user-credentials,#device-credentials').prop(
    'disabled', !$('#authentication').prop('checked')
  );
}

(function() {
  $('#authentication').change(function() {
    flipAuthenticationCombo();
  });
})();

/**
 * Display object modal for editing.
 * @param {type} type - Node or link.
 * @param {id} id - Id of the object to edit.
 */
function showObjectModal(type, id) { // eslint-disable-line no-unused-vars
  call(`/objects/get/${type}/${id}`, function(properties) {
    for (const [property, value] of Object.entries(properties)) {
      $(`#${type}-${property}`).val(value);
    }
    $('#connection-parameters-button').unbind('click');
    $('#connection-parameters-button').click(
      partial(connectionParametersModal, id)
    );
    $('#title').text(`Edit ${capitalize(type)} '${properties.name}'`);
    if (type == 'device') {
      call(`/views/get_logs/${id}`, function(logs) {
        $('#logs').text(logs);
      });
    }
    $(`#edit-${type}`).modal('show');
  });
}

/**
 * Edit object.
 * @param {type} type - Node or link.
 */
function editObject(type) { // eslint-disable-line no-unused-vars
  fCall('/objects/edit_object', `#edit-${type}-form`, function(result) {
    const mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
    if (typeof table !== 'undefined') {
      addObjectToTable(mode, type, result);
    }
    const message = `Object ${result.name}
    ${mode == 'edit' ? 'edited' : 'created'}.`;
    alertify.notify(message, 'success', 5);
    $(`#edit-${type}`).modal('hide');
  });
}

/**
 * Delete object.
 * @param {type} type - Node or link.
 * @param {id} id - Id of the object to delete.
 */
function deleteObject(type, id) { // eslint-disable-line no-unused-vars
  call(`/objects/delete/${type}/${id}`, function(result) {
    table.row($(`#${id}`)).remove().draw(false);
    alertify.notify(`Object '${result.name}' deleted.`, 'error', 5);
  });
}

/**
 * Add object to the datatable.
 * @param {mode} mode - Create or edit.
 * @param {type} type - Device or link.
 * @param {properties} properties - Properties of the object.
 */
function addObjectToTable(mode, type, properties) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    if (['longitude', 'latitude'].includes(fields[i])) {
      values.push(`${parseFloat(properties[fields[i]]).toFixed(2)}`);
    } else {
      values.push(`${properties[fields[i]]}`);
    }
  }

  // if it is a device, we add the "Connect" button.
  if (type == 'device') {
    values.push(`<button type="button" class="btn btn-success btn-xs"
    onclick="connectionParametersModal('${properties.id}')">Connect</button>`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showObjectModal('${type}', '${properties.id}')">Edit</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deleteObject('${type}', '${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${properties.id}`);
  }
}

/**
 * Display the object modal.
 * @param {type} type - Node or link.
 */
function showObjectTypeModal(type) { // eslint-disable-line no-unused-vars
  $('#title').text(`Create a New ${capitalize(type)}`);
  $(`#edit-${type}-form`).trigger('reset');
  $(`#edit-${type}`).modal('show');
}

/**
 * Open new tab at the provided URL.
 * @param {url} url - URL.
 */
function openUrl(url) {
  let win = window.open(url, '_blank');
  win.focus();
}

/**
 * Display the device connection modal.
 * @param {id} id - Device id.
 */
function connectionParametersModal(id) { // eslint-disable-line no-unused-vars
  $('#connection-button').unbind('click');
  $('#connection-button').click(partial(sshConnection, id));
  $('#connection-parameters-form').trigger('reset');
  flipAuthenticationCombo();
  $('#edit-device').modal('hide');
  $('#connection-parameters').modal('show');
}

/**
 * Start an SSH session to the device.
 * @param {id} id - Device id.
 */
function sshConnection(id) { // eslint-disable-line no-unused-vars
  const url = `/objects/connection/${id}`;
  fCall(url, '#connection-parameters-form', function(result) {
    let url = result.server_addr;
    if (!url) {
      url = `${window.location.protocol}//${window.location.hostname}`;
    }
    const terminal = result.redirection
      ? `${url}/terminal${result.port}/`
      : `${url}:${result.port}`;
    setTimeout(function() {
      openUrl(terminal);
    }, 300);
    const messageLink = `Click here to connect to ${result.device}.`;
    const link = `<a target='_blank' href='${terminal}'>${messageLink}</a>`;
    alertify.notify(link, 'success', 15);
    const warning = `Don't forget to turn off the pop-up blocker !`;
    alertify.notify(warning, 'error', 20);
    $('#connection-parameters').modal('hide');
  });
}
