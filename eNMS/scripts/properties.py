script_properties = (
    'id',
    'name',
    'type',
    'description',
)

netmiko_config_properties = script_properties + (
    'vendor',
    'operating_system',
    'content',
    'driver',
    'global_delay_factor'
)

napalm_config_properties = script_properties + (
    'vendor',
    'operating_system',
    'action',
    'content'
)

file_transfer_properties = script_properties + (
    'vendor',
    'operating_system',
    'driver',
    'source_file',
    'dest_file',
    'file_system',
    'direction',
    'overwrite_file',
    'disable_md5',
    'inline_transfer'
)

netmiko_validation_properties = script_properties + (
    'vendor',
    'operating_system',
    'driver',
    'command1',
    'command2',
    'command3',
    'content_match1',
    'content_match2',
    'content_match3',
    'content_match_regex1',
    'content_match_regex2',
    'content_match_regex3'
)

napalm_getters_properties = script_properties + (
    'getters',
    'content_match',
    'content_match_regex'
)

ansible_playbook_properties = script_properties + (
    'vendor',
    'operating_system',
    'playbook_path',
    'arguments',
    'content_match',
    'content_match_regex',
    'options',
    'pass_device_properties',
    'inventory_from_selection'
)

rest_call_properties = script_properties + (
    'call_type',
    'url',
    'payload',
    'content_match',
    'content_match_regex',
    'username',
    'password'
)

custom_properties = script_properties + (
    'vendor',
    'operating_system'
)

type_to_properties = {
    'netmiko_config': netmiko_config_properties,
    'napalm_config': napalm_config_properties,
    'file_transfer': file_transfer_properties,
    'netmiko_validation': netmiko_validation_properties,
    'napalm_getters': napalm_getters_properties,
    'ansible_playbook': ansible_playbook_properties,
    'rest_call': rest_call_properties,
    'custom_script': custom_properties
}
