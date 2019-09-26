/*
global
call: false
processInstance: false
*/

/**
 * Job Function for the Ansible Service Creation.
 * @param {id} id - Service id.
 */
// eslint-disable-next-line
function job(id) {
  call(`/scan_playbook_folder`, function(playbooks) {
    const fieldId = id ? `playbook_path-${id}` : "playbook_path";
    const field = $(`#ansible_playbook_service-${fieldId}`);
    playbooks.forEach((playbook) => {
      let option = document.createElement("option");
      option.textContent = option.value = playbook;
      field.append(option);
    });
    field.selectpicker("refresh");
    if (id) {
      call(`/get/ansible_playbook_service/${id}`, function(instance) {
        field.val(instance.playbook_path);
        field.selectpicker("refresh");
      });
    }
  });
}
