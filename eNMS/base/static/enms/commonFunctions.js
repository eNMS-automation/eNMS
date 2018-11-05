/*
global
alertify: false
*/

/**
 * Update link to the docs.
 * @param {url} url - URL pointing to the right page of the docs.
 */
function doc(url) { // eslint-disable-line no-unused-vars
  $('#doc-link').attr('href', url);
}

/**
 * Show modal.
 * @param {name} name - Modal name.
 */
function showModal(name) { // eslint-disable-line no-unused-vars
  $(`#${name}`).modal('show');
}

/**
 * Reset form and show modal.
 * @param {name} name - Modal name.
 */
function resetShowModal(name) { // eslint-disable-line no-unused-vars
  $(`#${name}-form`).trigger('reset');
  $(`#${name}`).modal('show');
}

/**
 * Returns partial function.
 * @param {function} func - any function
 * @return {function}
 */
function partial(func, ...args) { // eslint-disable-line no-unused-vars
  return function() {
    return func.apply(this, args);
  };
}

/**
 * Capitalize.
 * @param {string} string - Word.
 * @return {capitalizedString}
 */
function capitalize(string) { // eslint-disable-line no-unused-vars
    return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * jQuery Ajax Call.
 * @param {url} url - Url.
 * @param {callback} callback - Function to process results.
 */
function call(url, callback) { // eslint-disable-line no-unused-vars
  $.ajax({
    type: 'POST',
    url: url,
    success: function(results) {
      if (!results) {
        alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
      } else if (results.failure) {
        alertify.notify(results.error, 'error', 5);
      } else {
        callback(results);
      }
    },
  });
}

/**
 * jQuery Ajax Form Call.
 * @param {url} url - Url.
 * @param {form} form - Form.
 * @param {callback} callback - Function to process results.
 */
function fCall(url, form, callback) { // eslint-disable-line no-unused-vars
  console.log(form)
  if ($(form).parsley().validate()) {
    $.ajax({
      type: 'POST',
      url: url,
      data: $(form).serialize(),
      success: function(results) {
        if (!results) {
          alertify.notify('HTTP Error 403 – Forbidden', 'error', 5);
        } else if (results.failure) {
          alertify.notify(results.error, 'error', 5);
        } else {
          callback(results);
        }
      },
    });
  }
}

/**
 * Delete object.
 * @param {type} type - Node or link.
 * @param {id} id - Id of the object to delete.
 */
function deleteInstance(type, id) { // eslint-disable-line no-unused-vars
  call(`/delete/${type}/${id}`, function(result) {
    table.row($(`#${id}`)).remove().draw(false);
    alertify.notify(`${type} '${result.name}' deleted.`, 'error', 5);
  });
}

/**
 * Display type modal for creation.
 */
function showCreateModal(type) { // eslint-disable-line no-unused-vars
  $(`#edit-${type}-form`).trigger('reset');
  $(`#title-${type}`).text(`Create a New ${type}`);
  $(`#edit-${type}`).modal('show');
}

/**
 * Display instance modal for editing.
 * @param {id} id - Instance ID.
 * @param {duplicate} duplicate - Edit versus duplicate.
 */
function showTypeModal(type, id, duplicate) { // eslint-disable-line no-unused-vars
  call(`/get/${type}/${id}`, function(instance) {
    $(`#title-${type}`).text(
      `${duplicate ? 'Duplicate' : 'Edit'} ${type} '${instance.name}'`
    );
    if (duplicate) {
      instance.id = instance.name = '';
    }
    for (const [property, value] of Object.entries(instance)) {
      const propertyType = propertyTypes[property] || 'str';
      if (propertyType.includes('bool')) {
        $(`#${property}`).prop('checked', value);
      } else if (propertyType.includes('dict')) {
        $(`#${property}`).val(value ? JSON.stringify(value): '{}');
      } else {
        $(`#${property}`).val(value);
      }
    }
    $(`#edit-${type}`).modal('show');
  });
}


/**
 * Create or edit instance.
 */
function processData(type) { // eslint-disable-line no-unused-vars
  fCall(`/update/${type}`, `#edit-${type}-form`, function(instance) {
    const title = $(`#title-${type}`).text().startsWith('Edit');
    const mode = title ? 'edit' : 'create';
    addInstance(mode, type, instance);
    const message = `${type} '${instance.name}'
    ${mode == 'edit' ? 'edited' : 'created'}.`;
    alertify.notify(message, 'success', 5);
    $(`#edit-${type}`).modal('hide');
  });
}

/**
 * Add instance to datatable or edit line.
 * @param {mode} mode - Create or edit.
 * @param {instance} instance - Properties of the instance.
 */
function addInstance(mode, type, instance) {
  let values = [];
  for (let i = 0; i < fields.length; i++) {
    values.push(`${instance[fields[i]]}`);
  }
  tableActions(values, instance)
  if (mode == 'edit') {
    table.row($(`#${instance.id}`)).data(values);
  } else {
    const rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr('id', `${instance.id}`);
  }
}