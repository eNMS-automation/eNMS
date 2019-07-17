/*
global
*/

/**
 * Job Function for the Netmiko Multiline Validation Service.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function job(id) {
  console.log("test");
  const fieldId = id ? `anchor-${id}` : "anchor";
  const anchor = $(`#MultilineNetmikoValidationService-${fieldId}`);
  console.log(anchor)
  console.log(anchor.length);

}
