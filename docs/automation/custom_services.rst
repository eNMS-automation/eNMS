===============
Custom Services
===============

In addition to the services provided by default, you are free to create your own "custom" services.
Creating a custom services means adding a new python file in the ``eNMS/eNMS/services`` folder.
This python file must contain:

- A model class, where you define what the service parameters are, and what the service is doing (``job`` function).
- A form class, where you define what the service looks like in the GUI: the different fields in the service form and their corresponding validation.

Create a new service model
--------------------------

In ``eNMS/eNMS/services/examples``, you will find the file ``example_service.py`` with a service template
that you can use as starting point to create your own services. 

Swiss Army Knife Service
------------------------

Whenever your services require input parameters, eNMS automatically displays a form in the UI.
The "Swiss Army Knife Service" acts as a catch-all of utility methods that do not require GUI input.  It also serves to reduce the number of custom Services that a user might need, and thus reduces the complexity of performing database migrations across those Services.

Another use-case is to implement a service that will only exist as a single instance, and therefore does not need any variable parameter.
This can be done with the ``Swiss Army Knife Service``.

A "Swiss Army Knife Service" has only one parameter: a name. The function that will run when this service is scheduled is the one that carries the same name as the service itself.
The "Swiss Army Knife Service" ``job`` function can be seen as a "service multiplexer".

Let's take a look at how the ``Swiss Army Knife Service`` is implemented:

::

 class SwissArmyKnifeService(Service):

     __tablename__ = "swiss_army_knife_service"

     id = Column(Integer, ForeignKey("service.id"), primary_key=True)
     has_targets = Column(Boolean, default=False)

     __mapper_args__ = {"polymorphic_identity": "swiss_army_knife_service"}

     def job(self, *args):
         return getattr(self, self.name)(*args)

    def job1(self, payload):
        return {'success': True, 'result': ''}

    def job2(self, payload):
        return {'success': True, 'result': ''}

The ``job`` function of ``SwissArmyKnifeService`` will run the class method of ``SwissArmyKnifeService`` with the same name as the instance itself.

In other words, with the above code, you can create two instances of SwissArmyKnifeService from the web UI: one named "job1" and the other named "job2". The SwissArmyKnifeService class will take care of calling the right "job" function based on the name of the instance.

The SwissArmyKnifeService also has a parameter ``has_targets`` that defines whether or not the service will use the devices selected upon creating a new instance. If ``has_targets`` is selected, the SwissArmyKnifeService ``job`` function will take an additional device argument, and it will run the instance-name-specified job function on each selected device.  You can use the device properties (IP address, operating system, etc) however you need within the job function(s).

Helper function
---------------

In your custom python code, there is a number of function that are made available by eNMS and that you can reuse:

- Netmiko connection (``netmiko_connection = run.netmiko_connection(device)``)
give you a working netmiko connection, and takes care of caching the connection when running inside a workflow.
- Napalm connection (``napalm_connection = run.napalm_connection(device)``)
give you a working napalm connection, and takes care of caching the connection when running inside a workflow.
- Send email (``controller.send_email``) lets you send an email with optional attached file.

::

  controller.send_email(
      title,
      content,
      sender=sender,
      recipients=recipients,
      filename=filename,
      file_content=file_content
  )
