/*
global
eNMS: false
*/

// eslint-disable-next-line
function job(id) {
  const serviceClass = "netmiko_validation_service";
  eNMS.automation
    .field("auto_find_prompt", serviceClass, id)
    .on("change", function () {
      eNMS.automation
        .field("expect_string", serviceClass, id)
        .prop("disabled", this.checked);
    })
    .change();
}
