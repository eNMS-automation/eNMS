from eNMS.services.forms import (
    AnsibleServiceForm,
    NapalmConfigServiceForm,
    NapalmGettersForm,
    NetmikoConfigServiceForm,
    FileTransferServiceForm,
    NetmikoValidationForm,
    RestCallServiceForm
)

type_to_form = {
    'netmiko_config': NetmikoConfigServiceForm,
    'netmiko_validation': NetmikoValidationForm,
    'napalm_config': NapalmConfigServiceForm,
    'napalm_getters': NapalmGettersForm,
    'file_transfer': FileTransferServiceForm,
    'ansible_playbook': AnsibleServiceForm,
    'rest_call': RestCallServiceForm
}

type_to_name = {
    'netmiko_config': 'Netmiko Config',
    'netmiko_validation': 'Netmiko Validation',
    'napalm_config': 'NAPALM Config',
    'napalm_getters': 'NAPALM Getters',
    'file_transfer': 'File Transfer',
    'ansible_playbook': 'Ansible playbook',
    'rest_call': 'ReST Call',
    'custom_service': 'Custom service'
}
