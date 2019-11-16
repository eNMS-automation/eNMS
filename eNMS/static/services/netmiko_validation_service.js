/*
global
call: false
*/

/**
 * script to handle mutual exclusion of auto_find_prompt and expect_string
 * @param {id} id - Service id.
 */
// eslint-disable-next-line

function job(id) {
  const auto_find_prompt_fieldId = id
    ? `auto_find_prompt-${id}`
    : "auto_find_prompt";
  const auto_find_prompt_field = $(
    `#netmiko_validation_service-${auto_find_prompt_fieldId}`
  );
  const expect_string_fieldId = id ? `expect_string-${id}` : "expect_string";
  const expect_string_field = $(
    `#netmiko_validation_service-${expect_string_fieldId}`
  );
  auto_find_prompt_field
    .on("change", function() {
      expect_string_field.prop("disabled", this.checked);
    })
    .change();
}
