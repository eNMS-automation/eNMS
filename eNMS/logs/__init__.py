from eNMS.functions import add_classes
from eNMS.logs.models import Log, LogRule, SyslogServer

add_classes(Log, LogRule, SyslogServer)
