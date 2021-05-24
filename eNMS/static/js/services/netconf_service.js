// eslint-disable-next-line
function job(id) {
  const dropdownBaseId = "netconf_service-nc_type";
  const dropdownId = id ? `#${dropdownBaseId}-${id}` : `#${dropdownBaseId}`;
  let inputData = JSON.parse($("#input_data").val());
  $(dropdownId)
    .on("change", function () {
      operation = $(`${dropdownId} option:selected`).val();
      inputData["fields"].forEach((field) => {
        const displayField = inputData["netconf_type"][operation].includes(field);
        const display = displayField ? "block" : "none";
        const fieldBaseId = `#netconf_service-${field}`;
        $(`label[for=${field}]`).css("display", display);
        $(id ? `${fieldBaseId}-${id}` : fieldBaseId)
          .parent()
          .css("display", display);
      });
    })
    .change();
}
