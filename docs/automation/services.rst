========
Services
========

A service is a Python class that performs an action. You can define all the parameters you need as SQL Alchemy columns: eNMS will inspect the class parameters to automatically generate a service creation form in the web UI.

In ``eNMS/eNMS/services/services``, you will find the file ``example_service.py`` with a service template that you can use as starting point to create your own services. 
This file contains the following code :

::

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
  # - as a multiple selection drop-down list if the property is an SQL "List".
  # - as a single selection drop-down list in all other cases.
  # If you want to see a few examples of services, you can have a look at the
  # /netmiko, /napalm and /miscellaneous subfolders in /eNMS/eNMS/services.
  
  # Importing SQL Alchemy column types to handle all of the types of
  # form additions that the user could have.
  from sqlalchemy import (
      Boolean,
      Column,
      Float,
      ForeignKey,
      Integer,
      PickleType,
      String
  )
  from sqlalchemy.ext.mutable import MutableDict, MutableList
  
  from eNMS.services.models import Service, service_classes
  
  
  class ExampleService(Service):
  
      __tablename__ = 'ExampleService'
  
      id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
      # the "vendor" property will be displayed as a drop-down list, because
      # there is an associated "vendor_values" property in the class.
      vendor = Column(String)
      # the "operating_system" property will be displayed as a text area.
      operating_system = Column(String)
      # Text area
      an_integer = Column(Integer)
      # Text area
      a_float = Column(Float)
      # the "a_list" property will be displayed as a multiple selection drop-down
      # list, with the values contained in "a_list_values".
      a_list = Column(MutableList.as_mutable(PickleType))
      # Text area where a python dictionnary is expected
      a_dict = Column(MutableDict.as_mutable(PickleType))
      # "boolean1" and "boolean2" will be displayed as tick boxes in the GUI.
      boolean1 = Column(Boolean)
      boolean2 = Column(Boolean)
  
      # these values will be displayed in a single selection drop-down list,
      # for the property "a_list".
      vendor_values = [
          ('cisco', 'Cisco'),
          ('juniper', 'Juniper'),
          ('arista', 'Arista')
      ]
  
      # these values will be displayed in a multiple selection drop-down list,
      # for the property "a_list".
      a_list_values = [
          ('value1', 'Value 1'),
          ('value2', 'Value 2'),
          ('value3', 'Value 3')
      ]
  
      __mapper_args__ = {
          'polymorphic_identity': 'example_service',
      }
  
      def job(self, task, incoming_payload):
          # The "job" function is called when the service is executed.
          # The parameters of the service can be accessed with self (self.vendor,
          # self.boolean1, etc)
          # The target devices can be computed via "task.compute_targets()".
          # You can look at how default services (netmiko, napalm, etc.) are
          # implemented in the /services subfolders (/netmiko, /napalm, etc).
          results = {'success': True, 'result': 'nothing happened'}
          for device in task.compute_targets():
              results[device.name] = True
          # The results is a dictionnary that will be displayed in the logs.
          # It must contain at least a key "success" that indicates whether
          # the execution of the service was a success or a failure.
          # In a workflow, the "success" value will determine whether to move
          # forward with a "Sucess" edge or a "Failure" edge.
          return results
  
  
  service_classes['Example Service'] = ExampleService

Add new services
----------------

All default services mentioned below are located in the ``eNMS/source/services/services`` folder. 
After adding a new custom service, you must reload the application.
Inside that folder, you are free to create subfolders to organize your own services any way you want: eNMS will automatically detect all python files.

Netmiko configuration service
----------------------------

Uses Netmiko to send list of commands to be configured on the devices.
A **driver** must be selected among all available netmiko drivers.

.. image:: /_static/automation/services/netmiko_configuration_service.png
   :alt: Netmiko configuration service
   :align: center

Netmiko File transfer service
----------------------------

A file transfer service sends a file to a device, or retrieve a file from a device.
It relies on Netmiko file transfer functions.

.. image:: /_static/automation/services/file_transfer_service.png
   :alt: Netmiko file transfer service
   :align: center

.. caution:: File-transfer services only works for IOS, IOS-XE, IOS-XR, NX-OS and Junos.

Netmiko validation service
-------------------------

A ``Netmiko validation`` service is used to check the state of a device, in a workflow (see the ``Workflow`` section for examples about how it is used).

There are 3 ``command`` field and 3 ``pattern`` field. For each couple of command/pattern field, eNMS will check if the expected pattern can be found in the output of the command.
If the result is positive for all 3 couples, the service will return ``True`` (allowing the workflow to go forward, following the ``success`` edges), else it will return ``False``.

.. image:: /_static/automation/services/netmiko_validation_service.png
   :alt: Netmiko validation service
   :align: center

NAPALM configuration service
---------------------------

This type of service uses NAPALM to update the configuration of a device.

There are two types of operations:
  - ``load merge``: add the service configuration to the existing configuration of the target.
  - ``load replace``: replace the configuration of the target with the service configuration.

.. image:: /_static/automation/services/napalm_configuration_service.png
   :alt: NAPALM configuration service
   :align: center

.. note:: The NAPALM driver used by eNMS is the one you configure in the "Operating System" property of a device.
The NAPALM drivers name must be respected: ``ios, iosxr, nxos, junos, eos``.

.. note:: This service does not by itself commit the configuration. To do so, a ``NAPALM action`` service must be used (see below).

NAPALM action service
--------------------

``NAPALM action`` services do not have to be created: they are created by default when eNMS runs for the first time.
There are three actions:
  - ``commit``: commits the changes pushed with ``load replace`` or ``load merge``.
  - ``discard``: discards the changes before they were committed.
  - ``rollback``: rollbacks the changes after they have been committed.

NAPALM getters service
---------------------

A ``NAPALM getters`` service is a list of getters which output is displayed in the logs.

.. image:: /_static/automation/services/napalm_getters_service.png
   :alt: NAPALM getters service
   :align: center

.. note:: just like with the ``NAPALM configuration`` services, the NAPALM driver used by eNMS is the one configured in the "Operating System" property of a device. The NAPALM drivers name must be respected: ``ios, iosxr, nxos, junos, eos``.

Ansible playbook service
-----------------------

An ``Ansible playbook`` service sends an ansible playbook to the devices.

.. image:: /_static/automation/services/ansible_playbook_service.png
   :alt: Ansible service
   :align: center
