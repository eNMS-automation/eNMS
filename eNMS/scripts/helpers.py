from eNMS.scripts.forms import (
    AnsibleScriptForm,
    NapalmConfigScriptForm,
    NapalmGettersForm,
    NetmikoConfigScriptForm,
    FileTransferScriptForm,
    NetmikoValidationForm,
    RestCallScriptForm
)

type_to_form = {
    'netmiko_config': NetmikoConfigScriptForm,
    'napalm_config': NapalmConfigScriptForm,
    'napalm_getters': NapalmGettersForm,
    'file_transfer': FileTransferScriptForm,
    'netmiko_validation': NetmikoValidationForm,
    'ansible_playbook': AnsibleScriptForm,
    'rest_call': RestCallScriptForm
}

type_to_name = {
    'netmiko_config': 'Netmiko Config',
    'napalm_config': 'NAPALM Config',
    'napalm_getters': 'NAPALM Getters',
    'file_transfer': 'File Transfer',
    'netmiko_validation': 'Validation',
    'ansible_playbook': 'Ansible playbook',
    'rest_call': 'ReST Call',
    'custom_script': 'Custom script'
}
