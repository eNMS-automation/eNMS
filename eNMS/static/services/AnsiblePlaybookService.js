function job(id) {
  call(`/scan_playbook_folder`, function(playbooks) {
    const fieldId = id ? `playbook_path-${id}` : "playbook_path";
    field = $(`#AnsiblePlaybookService-${fieldId}`);
    playbooks.forEach((playbook) => {
      let option = document.createElement("option");
      option.textContent = option.value = playbook;
      field.appendChild(option);
    });
    field.selectpicker("refresh");
  });
}