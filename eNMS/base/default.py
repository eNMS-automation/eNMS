from eNMS import db
from eNMS.admin.models import Parameters, SyslogServer
from eNMS.base.custom_base import factory
from eNMS.base.helpers import integrity_rollback
from eNMS.objects.models import Pool

default_pools = (
    {'name': 'All objects'},
    {'name': 'Nodes only', 'link_name': '^$', 'link_name_regex': True},
    {'name': 'Links only', 'node_name': '^$', 'node_name_regex': True}
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
