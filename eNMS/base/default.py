from werkzeug.datastructures import ImmutableMultiDict

from eNMS import db
from eNMS.admin.models import Parameters, SyslogServer
from eNMS.base.custom_base import factory
from eNMS.base.helpers import integrity_rollback
from eNMS.objects.models import Pool

default_pools = (
    {'name': 'All objects'},
    {'name': 'Devices only', 'link_name': '^$', 'link_name_regex': True},
    {'name': 'Links only', 'device_name': '^$', 'device_name_regex': True}
)


@integrity_rollback
def create_default_pools():
    for pool in default_pools:
        pool = factory(Pool, **pool)


@integrity_rollback
def create_default_parameters():
    parameters = Parameters()
    db.session.add(parameters)
    db.session.commit()


@integrity_rollback
def create_default_syslog_server():
    syslog_server = SyslogServer(ip_address='0.0.0.0', port=514)
    db.session.add(syslog_server)
    db.session.commit()

# Default scripts

create_vrf_TEST = ImmutableMultiDict([
    ('name', 'create_vrf_TEST'),
    ('description', 'Create a vrf "TEST"'),
    ('vendor', 'Cisco'),
    ('operating_system', 'IOS'),
    ('content_type', 'simple'),
    ('driver', 'cisco_ios'),
    ('global_delay_factor', '1.0'),
    ('content', 'ip vrf TEST')
])

remove_vrf_TEST = ImmutableMultiDict([
    ('name', 'remove_vrf_TEST'),
    ('description', 'Remove vrf "TEST"'),
    ('vendor', 'Cisco'),
    ('operating_system', 'IOS'),
    ('content_type', 'simple'),
    ('driver', 'cisco_ios'),
    ('global_delay_factor', '1.0'),
    ('content', 'no ip vrf TEST')
])

