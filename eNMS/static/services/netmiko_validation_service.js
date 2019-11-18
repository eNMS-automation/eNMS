/*
global
field: false
*/

// eslint-disable-next-line
function job(id) {
  field("auto_find_prompt", type, id)
    .on("change", function() {
      field("expect_string", type, id).prop("disabled", this.checked);
    })
    .change();
}
