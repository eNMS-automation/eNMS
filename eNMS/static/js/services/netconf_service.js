// eslint-disable-next-line
function job(id) {
  const dropdownBaseId = "#netconf_service-nc_type";
  const dropdownId = id ? `${dropdownBaseId}-${id}` : dropdownBaseId;
  let inputData = JSON.parse($("#input_data").val());
  $(dropdownId)
    .on("change", function() {
      const operation = $(`${dropdownId} option:selected`).val();
      inputData["fields"].forEach((field) => {
        const fieldBaseId = `#netconf_service-${field}-div`;
        const fieldId = id ? `${fieldBaseId}-${id}` : fieldBaseId;
        const display = inputData["netconf_type"][operation].includes(field);
        $(fieldId).css("display", display ? "block" : "none");
      });
    })
    .change();
}
