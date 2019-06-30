function job() {
  call(`/scan_playbook_folder`, function(playbooks) {
    console.log(playbooks);
  });
}