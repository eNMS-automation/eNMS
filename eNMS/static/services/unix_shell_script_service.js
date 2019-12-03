/*
global
field: false
*/

// eslint-disable-next-line
function job(id) {
  const serviceType = "unix_shell_script_service";
  field("auto_find_prompt", serviceType, id)
    .on("change", function() {
      field("expect_string", serviceType, id).prop("disabled", this.checked);
    })
    .change();
}
