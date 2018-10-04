# This class serves as a template example for the user to understand
# how to implement their own custom services to eNMS.
# It can be removed if you are deploying eNMS in production.

# Each new service must inherit from the "Service" class.
# eNMS will automatically generate a form in the web GUI by looking at the
# SQL parameters of the class.
# By default, a property (String, Float, Integer) will be displayed in the GUI
# with a text area for the input.
# If the property in a Boolean, it will be displayed as a tick box instead.
# If the class contains a "property_name_values" property with a list of
# values, it will be displayed:
# - as a multiple selection list if the property is an SQL "MutableList".
# - as a single selection drop-down list in all other cases.
# If you want to see a few examples of services, you can have a look at the
# /netmiko, /napalm and /miscellaneous subfolders in /eNMS/eNMS/services.

# Importing SQL Alchemy column types to handle all of the types of
# form additions that the user could have.
from sqlalchemy import ForeignKey, Integer,


from eNMS.services.models import Service, service_classes


class ProcessPayloadService(Service):

    __tablename__ = 'ProcessPayloadService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'process_payload_service',
    }

    def job(self, task, incoming_payload):
        print(incoming_payload)
        results = {'success': True, 'result': 'nothing happened', 'test': incoming_payload}
        return results


service_classes['Process Payload Service'] = ProcessPayloadService
