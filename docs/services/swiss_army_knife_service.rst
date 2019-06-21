========================
Swiss Army Knife Service
========================

Whenever your services require input parameters, eNMS automatically displays a form in the UI.
The "Swiss Army Knife Service" acts as a catch-all of utility methods that do not require GUI input.  It also serves to reduce the number of custom Services that a user might need, and thus reduces the complexity of performing database migrations across those Services.

Another use-case is to implement a service that will only exist as a single instance, and therefore does not need any variable parameter.
This can be done with the ``Swiss Army Knife Service``.

A "Swiss Army Knife Service" has only one parameter: a name. The function that will run when this service is scheduled is the one that carries the same name as the service itself.
The "Swiss Army Knife Service" ``job`` function can be seen as a "job multiplexer".

Let's take a look at how the ``Swiss Army Knife Service`` is implemented:

::

 class SwissArmyKnifeService(Service):

     __tablename__ = "SwissArmyKnifeService"

     id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
     has_targets = Column(Boolean, default=False)

     __mapper_args__ = {"polymorphic_identity": "SwissArmyKnifeService"}

     def job(self, *args):
         return getattr(self, self.name)(*args)

    def job1(self, payload):
        return {'success': True, 'result': ''}

    def job2(self, payload):
        return {'success': True, 'result': ''}

The ``job`` function of ``SwissArmyKnifeService`` will run the class method of ``SwissArmyKnifeService`` with the same name as the instance itself.

In other words, with the above code, you can create two instances of SwissArmyKnifeService from the web UI: one named "job1" and the other named "job2". The SwissArmyKnifeService class will take care of calling the right "job" function based on the name of the instance.

The SwissArmyKnifeService also has a parameter ``has_targets`` that defines whether or not the service will use the devices selected upon creating a new instance. If ``has_targets`` is selected, the SwissArmyKnifeService ``job`` function will take an additional device argument, and it will run the instance-name-specified job function on each selected device.  You can use the device properties (IP address, operating system, etc) however you need within the job function(s).
