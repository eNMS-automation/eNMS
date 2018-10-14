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
 */
function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}