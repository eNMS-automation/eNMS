from os.path import join
from werkzeug.datastructures import ImmutableMultiDict
from xlrd import open_workbook
from xlrd.biffh import XLRDError

from eNMS import db
from eNMS.admin.models import Parameters, SyslogServer
from eNMS.base.custom_base import factory
from eNMS.base.helpers import integrity_rollback
from eNMS.objects.models import Pool
from eNMS.objects.routes import process_kwargs

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


@integrity_rollback
def create_default_network_topology(app):
    with open(join(app.path, 'projects', 'defaults.xls'), 'rb') as f:
        book = open_workbook(file_contents=f.read())
        for object_type in ('Device', 'Link'):
            try:
                sheet = book.sheet_by_name(object_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                values = dict(zip(properties, sheet.row_values(row_index)))
                cls, kwargs = process_kwargs(app, **values)
                factory(cls, **kwargs).serialized
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

