/*
global
*/

/**
 * Job Function for the Netmiko Multiline Validation Service.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function job(id) {

  const fieldId = id ? `playbook_path-${id}` : "playbook_path";
  const field = $(`#AnsiblePlaybookService-${fieldId}`);

}
