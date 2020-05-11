/*
global
eNMS: false
*/

// eslint-disable-next-line
function job(id) {
  const serviceType = "unix_shell_script_service";
  eNMS.automation
    .field("auto_find_prompt", serviceType, id)
    .on("change", function () {
      eNMS.automation
        .field("expect_string", serviceType, id)
        .prop("disabled", this.checked);
    })
    .change();
}
