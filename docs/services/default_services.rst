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
  # - as a multiple selection list if the property is an SQL "MutableList".
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
      # the "a_list" property will be displayed as a multiple selection list.
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

When the application starts, it loads all python files in ``eNMS/eNMS/services/services``, and adds all models to the database.
You can create instances of that service from the web UI. eNMS looks at the class parameters (SQL Alchemy columns) to auto-generate a form for the user to create new instances.

For the ``ExampleService`` class displayed above, here is the associated auto-generated form:

.. image:: /_static/automation/services/example_service.png
   :alt: Example service
   :align: center

The rules for the auto-generation of forms are the following:
  - A String, Integer or Float property is by default displayed as a text area. However, if the service class has another property which name is "<property_name>_values", eNMS will generate a drop-down list to choose a value from instead. In the aforementioned example, ``operating_system`` is a String column that will be displayed as a text area in the web UI. On the other hand, ``vendor`` is a String column and the class has a ``vendor_values`` property that contains a list of possible values: the ``vendor`` property will be displayed as a (single-selection) drop-down list.
  - A Boolean property is displayed as a tick box.
  - A MutableList property is displayed as a multi-selection list. It must have an associated "_values" property containing the list of values that can be selected.
  - A MutableDict property is displayed as a text area. You can write a dictionnary in that text area: it will be converted to an actual python dictionnary.

Inside the ``eNMS/eNMS/services/services`` folder, you are free to create subfolders to organize your own services any way you want: eNMS will automatically detect all python files. After adding a new custom service, you must reload the application before it appears in the web UI.

eNMS comes with a list of "default" services based on network automation frameworks such as ``netmiko``, ``napalm`` and ``ansible``.

Service Management
------------------

All services are displayed in the :guilabel:`services/service_management` page in the ``Microservices`` section.
They can be scheduled (see the ``scheduling`` section of the doc for more information) and deleted.

.. image:: /_static/automation/services/service_management.png
   :alt: Service Editor
   :align: center

Service Editor
--------------

.. image:: /_static/automation/services/service_editor.png
   :alt: Service Editor
   :align: center

You can create and edit all services from the :guilabel:`services/service_editor` page in the ``Microservices`` section.
The first drop-down list allows the user to choose a class of service (like the class ``ExampleService`` discussed previously).
The second one contains all instances for that class of service (if there are no such instance, it is empty).
The form displayed below these two lists is the auto-generated form : it can be used both as a way to create new services, or edit existing ones.

Netmiko Configuration Service
----------------------------

Uses Netmiko to send a list of commands to be configured on the devices.
A **driver** must be selected among all available netmiko drivers.
The list of netmiko drivers is built upon netmiko ``CLASS_MAPPER_BASE`` in ``ssh_dispatcher.py`` (https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py#L69).

.. image:: /_static/automation/services/netmiko_configuration.png
   :alt: Netmiko Configuration service
   :align: center

Netmiko File Transfer Service
----------------------------

A file transfer service sends a file to a device, or retrieve a file from a device.
It relies on Netmiko file transfer functions.

.. image:: /_static/automation/services/netmiko_file_transfer.png
   :alt: Netmiko File Transfer service
   :align: center

.. caution:: File-transfer services only works for IOS, IOS-XE, IOS-XR, NX-OS and Junos.

Netmiko Validation Service
-------------------------

A ``Netmiko validation`` service is used to check the state of a device, in a workflow (see the ``Workflow`` section for examples about how it is used).

There are 3 ``command`` field and 3 ``pattern`` field. For each couple of command/pattern field, eNMS will check if the expected pattern can be found in the output of the command.
If the result is positive for all 3 couples, the service will return ``True`` (allowing the workflow to go forward, following the ``success`` edges), else it will return ``False``.
The values for a ``pattern`` field can also be a regular expression.

.. image:: /_static/automation/services/netmiko_validation.png
   :alt: Netmiko validation service
   :align: center

Napalm Configuration service
----------------------------

This type of service uses Napalm to update the configuration of a device.

There are two types of operations:
  - ``load merge``: add the service configuration to the existing configuration of the target.
  - ``load replace``: replace the configuration of the target with the service configuration.

.. image:: /_static/automation/services/napalm_configuration.png
   :alt: Napalm configuration service
   :align: center

Napalm Rollback Service
-----------------------

Use Napalm to Rollback a configuration.

.. image:: /_static/automation/services/napalm_rollback.png
   :alt: Napalm Rollback service
   :align: center

Napalm getters service
----------------------

A ``Napalm Getters`` service is a list of getters which output is displayed in the logs.

.. image:: /_static/automation/services/napalm_getters.png
   :alt: Napalm Getters service
   :align: center

Ansible Playbook Service
------------------------

An ``Ansible Playbook`` service sends an ansible playbook to the devices.

.. image:: /_static/automation/services/ansible_playbook.png
   :alt: Ansible Playbook service
   :align: center

ReST Call Service
-----------------

Send a ReST call (GET, POST, PUT or DELETE) to an URL with optional payload.

.. image:: /_static/automation/services/rest_call.png
   :alt: ReST Call service
   :align: center