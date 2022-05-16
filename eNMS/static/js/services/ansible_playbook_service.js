/*
global
eNMS: false
*/

// eslint-disable-next-line
function job(id) {
  eNMS.base.call({
    url: `/scan_playbook_folder`,
    callback: function (playbooks) {
      const fieldId = id ? `playbook_path-${id}` : "playbook_path";
      const field = $(`#ansible_playbook_service-${fieldId}`);
      playbooks.forEach((playbook) => {
        let option = document.createElement("option");
        option.textContent = option.value = playbook;
        field.append(option);
      });
      field.selectpicker("refresh");
      if (id) {
        eNMS.base.call({
          url: `/get/ansible_playbook_service/${id}`,
          callback: function (instance) {
            field.val(instance.playbook_path);
            field.selectpicker("refresh");
          },
        });
      }
    },
  });
}
