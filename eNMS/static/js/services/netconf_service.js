// eslint-disable-next-line
function job(id) {
  setTimeout(() => {
    const dropdownBaseId = "netconf_service-nc_type";
    const dropdownId = id ? `#${dropdownBaseId}-${id}` : `#${dropdownBaseId}`;
    const dropdownObject = $(dropdownId)
    let inputData = JSON.parse($("#input_data").val());
    const fields = inputData["fields"];
    const netconfType = inputData["netconf_type"];
    let operation = dropdownObject.val();
    dropdownObject.on("change", function() {
      operation = $(`${dropdownId} option:selected`).val();
      console.log(fields)
      updateElements(fields, netconfType, operation);
    }).change();
  }, 500);

  // HELPERS
  function updateElements(fieldList, netconfTypes, selectedType) {
    // make all fields invisible
    fieldList.forEach((field) => {
      const display = netconfTypes[selectedType].includes(field) ? "block" : "none";
      const fieldBaseId = `#netconf_service-${field}`
      $(`label[for=${field}]`).css("display", display);
      $(id ? `${fieldBaseId}-${id}` : fieldBaseId).parent().css("display", display);
    });
  }

}
