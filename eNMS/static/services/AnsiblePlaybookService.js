/*
global
call: false
*/

/**
 * Job Function for the Ansible Service Creation.
 * @param {id} id - Job id.
 */
// eslint-disable-next-line
function job(id) {
  call(`/scan_playbook_folder`, function(playbooks) {
    const fieldId = id ? `playbook_path-${id}` : "playbook_path";
    const field = $(`#AnsiblePlaybookService-${fieldId}`);
    playbooks.forEach((playbook) => {
      let option = document.createElement("option");
      option.textContent = option.value = playbook;
      field.append(option);
    });
    field.selectpicker("refresh");
  });
}
