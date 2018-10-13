========
Services
========

A service is a Python class that performs an action. You can define all the parameters you need as SQL Alchemy columns: eNMS will inspect the class parameters to automatically generate a service creation form in the web UI.

In ``eNMS/eNMS/automation/services/examples``, you will find the file ``example_service.py`` with a service template that you can use as starting point to create your own services. 
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
  
  from eNMS.automation.models import Service, service_classes
  
  
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
      # the "a_list" property will be displayed as a multiple selection list
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
  
      # these values will be displayed in a multiple selection list,
      # for the property "a_list".
      a_list_values = [
          ('value1', 'Value 1'),
          ('value2', 'Value 2'),
          ('value3', 'Value 3')
      ]
  
      __mapper_args__ = {
          'polymorphic_identity': 'example_service',
      }
  
      def job(self, payload):
          # The "job" function is called when the service is executed.
          # The parameters of the service can be accessed with self (self.vendor,
          # self.boolean1, etc)
          # You can look at how default services (netmiko, napalm, etc.) are
          # implemented in the /services subfolders (/netmiko, /napalm, etc).
          # "results" is a dictionnary that will be displayed in the logs.
          # It must contain at least a key "success" that indicates whether
          # the execution of the service was a success or a failure.
          # In a workflow, the "success" value will determine whether to move
          # forward with a "Success" edge or a "Failure" edge.
          return {'success': True, 'result': 'example'}
  
  
  service_classes['example_service'] = ExampleService

When the application starts, it loads all python files in ``eNMS/eNMS/automation/services``, and adds all models to the database.
You can create instances of that service from the web UI.

eNMS looks at the class parameters (SQL Alchemy columns) to auto-generate a form for the user to create new instances of that service.

For the ``ExampleService`` class displayed above, the SQL columns are the following ones:

::

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

Here is the associated auto-generated form:

.. image:: /_static/services/service_system/example_service.png
   :alt: Example service
   :align: center

The rules for the auto-generation of service forms are the following:
  - A String, Integer or Float property is by default displayed as a text area. However, if the service class has another property which name is ``<property_name>_values``, eNMS will generate a drop-down list to choose a value from instead. In the aforementioned example, ``operating_system`` is a String column that will be displayed as a text area in the web UI. On the other hand, ``vendor`` is a String column and the class has a ``vendor_values`` property that contains a list of possible values: the ``vendor`` property will be displayed as a (single-selection) drop-down list.
  - A Boolean property is displayed as a checkbox.
  - A MutableList property is displayed as a multi-selection list. It must have an associated "_values" property containing the list of values that can be selected.
  - A MutableDict property is displayed as a text area. You can write a dictionnary in that text area: it will be converted to an actual python dictionnary.

Inside the ``eNMS/eNMS/automation/services`` folder, you are free to create subfolders to organize your own services any way you want: eNMS will automatically detect all python files. After adding a new custom service, you must reload the application before it appears in the web UI.

eNMS comes with a list of "default" services based on network automation frameworks such as ``netmiko``, ``napalm``, ``nornir`` and ``ansible``.

Service Management
------------------

All services are displayed in the :guilabel:`automation/service_management` page in the ``Automation`` section.

.. image:: /_static/services/service_system/service_management.png
   :alt: Service Management page
   :align: center

From the :guilabel:`automation/service_management` page, you can:

  - Start a service (``Run`` button)
  - View the logs of the service.
  - Edit the service properties.
  - Compare the logs of the service.
  - Delete the service.

Clicking on the ``Compare`` button generates a line-by-line diff of the service logs between any two runs.
Here's a comparison of a ``Napalm get_facts`` service:

.. image:: /_static/services/service_system/service_compare_logs.png
   :alt: Compare logs
   :align: center

Service devices
---------------

When you create a new service, the form will also contain multiple selection fields for you to select "target devices".

.. image:: /_static/services/service_system/target_selection.png
   :alt: Target selection
   :align: center

The service will run on all selected devices in parallel (multiprocessing). If you select pools, it will run on the union of all devices in the selected pools.
Some services have no target device at all, depending on what the service does.