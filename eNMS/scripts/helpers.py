from eNMS.scripts.forms import (
    AnsibleScriptForm,
    NapalmConfigScriptForm,
    NapalmGettersForm,
    NetmikoConfigScriptForm,
    FileTransferScriptForm,
    NetmikoValidationForm,
)

type_to_form = {
    'netmiko_config': NetmikoConfigScriptForm,
    'napalm_config': NapalmConfigScriptForm,
    'napalm_getters': NapalmGettersForm,
    'file_transfer': FileTransferScriptForm,
    'netmiko_validation': NetmikoValidationForm,
    'ansible_playbook': AnsibleScriptForm
}

type_to_name = {
    'netmiko_config': 'Netmiko Config',
    'napalm_config': 'NAPALM Config',
    'napalm_getters': 'NAPALM Getters',
    'file_transfer': 'File Transfer',
    'netmiko_validation': 'Validation',
    'ansible_playbook': 'Ansible playbook',
    'custom_script': 'Custom script'
}