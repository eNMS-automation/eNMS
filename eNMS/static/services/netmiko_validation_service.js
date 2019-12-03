/*
global
field: false
*/

// eslint-disable-next-line
function job(id) {
  const serviceClass = "netmiko_validation_service";
  field("auto_find_prompt", serviceClass, id)
    .on("change", function() {
      field("expect_string", serviceClass, id).prop("disabled", this.checked);
    })
    .change();
}
