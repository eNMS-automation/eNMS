===============
Create a script
===============

Scripts are created from the :guilabel:`Scripts` menu. 
There are different types of script available in eNMS:

Configuration script
--------------------

There are two types of configuration:
  - ``text-based``: a list of configuration commands to be sent to the device.
  - ``template-based``: the script is a Jinja2 template. A .YAML file containing all parameters must be provided.
A configuration script can be sent with either NAPALM, or Netmiko.

.. image:: /_static/automation/create/configuration_script.png
   :alt: test
   :align: center

File transfer script
--------------------

A file transfer script is designed to send a script to a device, or retrieve a script from a device.
It relies on Netmiko file transfer functions. 

.. image:: /_static/automation/create/file_transfer_script.png
   :alt: test
   :align: center

.. caution:: File-transfer scripts only works for IOS, IOS-XE, IOS-XR, NX-OS and Junos.

Ansible script
--------------

work in progress