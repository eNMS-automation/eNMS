// eslint-disable-next-line
function job(id) {
  setTimeout(() => {
    const dropdownBaseId = "netconf_service-nc_type";
    const dropdownId = id ? `${dropdownBaseId}-${id}` : dropdownBaseId;
    const dropdownObject = $(dropdownId) 
    let inputData = JSON.parse($("#input_data").val());
    const fields = inputData["fields"];
    const netconfType = inputData["netconf_type"];
    let operation = dropdownObject.val();
    updateElements(fields, netconfType, operation);
    dropdownObject.change(() => {
      operation = $(`#${dropdownId} option:selected`).val();
      updateElements(fields, netconfType, operation);
    });
  }, 50);

  // HELPERS
  function updateElements(fieldList, netconfTypes, selectedType) {
    // make all fields invisible
    for (let key in fieldList) {
      if ({}.hasOwnProperty.call(fieldList, key)) {
        hideElement(fieldList[key]);
      }
    }

    // enable fields per selection
    let fieldsToShow = netconfTypes[selectedType];
    for (let key in fieldsToShow) {
      if ({}.hasOwnProperty.call(fieldsToShow, key)) {
        showElement(fieldsToShow[key]);
      }
    }
  }

  function hideElement(name) {
    // disables visibility for a field
    $(`label[for=${name}]`).hide();
    if (id) {
      $(`#netconf_service-${name}-${id}`)
        .parent()
        .hide();
    } else {
      $(`#netconf_service-${name}`)
        .parent()
        .hide();
    }
  }

  function showElement(name) {
    // enables visibility for a field
    $(`label[for=${name}]`).show();
    if (id) {
      $(`#netconf_service-${name}-${id}`)
        .parent()
        .show();
    } else {
      $(`#netconf_service-${name}`)
        .parent()
        .show();
    }
  }

  function getSelectedValue(dropdownId, id) {
    // returns the currently selected value for a dropdown
    let value = null;
    if (id) {
      value = $(`#${dropdownId}-${id} option:selected`).val();
    } else {
      value = 
    }
    return value;
  }

}
