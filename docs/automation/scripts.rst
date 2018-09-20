=======
Scripts
=======

Scripts are created from the :guilabel:`Scripts` menu. 
The following types of service are available in eNMS.

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

Add new services
---------------

All default services mentioned above are located in the ``eNMS/source/services/services`` folder. New services can be added to the folder by reusing the same base template:

::

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
  
  
  class AService(Service):
  
      __tablename__ = 'AService'
  
      id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
      vendor = Column(String)
      operating_system = Column(String)
      an_integer = Column(Integer)
      a_float = Column(Float)
      a_list = Column(MutableList.as_mutable(PickleType))
      a_dict = Column(MutableDict.as_mutable(PickleType))
      boolean1 = Column(Boolean)
      boolean2 = Column(Boolean)
  
      vendor_values = [
          ('cisco', 'Cisco'),
          ('juniper', 'Juniper'),
          ('arista', 'Arista')
      ]
  
      a_list_values = [
          ('value1', 'Value 1'),
          ('value2', 'Value 2'),
          ('value3', 'Value 3')
      ]
  
      __mapper_args__ = {
          'polymorphic_identity': 'a_service',
      }
  
      def __init__(self, **kwargs):
          super().__init__(**kwargs)
  
      def job(self, *args):
          return True, 'a', 'a'
  
  
  service_classes['A Service'] = AService


After adding a new custom service, you must reload the application.
Inside that folder, you are free to create subfolders to organize your own services any way you want: eNMS will automatically detect all python files. Based on the parameters of the services you create, eNMS will automatically generate the associated form in the "Service Editor" webpage.