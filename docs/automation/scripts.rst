=======
Scripts
=======

Scripts are created from the :guilabel:`Scripts` menu. 
The following types of script are available in eNMS.

Netmiko configuration script
----------------------------

There are two types of Netmiko configuration scripts:
  - **"show" commands**: a list of “show commands” which output will be displayed in the logs.
  - **configuration**: a list of commands to be configured on the devices.

For each type, the content of the script can be:
  - ``text-based``: a list of configuration commands to be sent to the device.
  - ``template-based``: the script is a Jinja2 template. A .YAML file containing all parameters must be provided.

Finally, a **driver** must be selected among all available netmiko drivers.

.. image:: /_static/automation/scripts/netmiko_configuration_script.png
   :alt: Netmiko configuration script
   :align: center

Netmiko File transfer script
----------------------------

A file transfer script sends a file to a device, or retrieve a file from a device.
It relies on Netmiko file transfer functions.

If you want to send a file to a device, you must place the file in the ``eNMS/file_transfer`` folder.

.. image:: /_static/automation/scripts/file_transfer_script.png
   :alt: Netmiko file transfer script
   :align: center

.. caution:: File-transfer scripts only works for IOS, IOS-XE, IOS-XR, NX-OS and Junos.

Netmiko validation script
-------------------------

A ``Netmiko validation`` script is used to check the state of a device, in a workflow (see the ``Workflow`` section for examples about how it is used).

There are 3 ``command`` field and 3 ``pattern`` field. For each couple of command/pattern field, eNMS will check if the expected pattern can be found in the output of the command.
If the result is positive for all 3 couples, the script will return ``True`` (allowing the workflow to go forward, following the ``success`` edges), else it will return ``False``.

.. image:: /_static/automation/scripts/netmiko_validation_script.png
   :alt: Netmiko validation script
   :align: center

NAPALM configuration script
---------------------------

This type of script uses NAPALM to update the configuration of a device.

There are two types of operations:
  - ``load merge``: add the script configuration to the existing configuration of the target.
  - ``load replace``: replace the configuration of the target with the script configuration.

Just like with the ``Netmiko configuration`` script, a configuration can be either ``text-based``, or ``template-based``.

.. image:: /_static/automation/scripts/napalm_configuration_script.png
   :alt: NAPALM configuration script
   :align: center

.. note:: The NAPALM driver used by eNMS is the one you configure in the "Operating System" property of a node.
The NAPALM drivers name must be respected: ``ios, iosxr, nxos, junos, eos``.

.. note:: This script does not by itself commit the configuration. To do so, a ``NAPALM action`` script must be used (see below).

NAPALM action script
--------------------

``NAPALM action`` scripts do not have to be created: they are created by default when eNMS runs for the first time.
There are three actions:
  - ``commit``: commits the changes pushed with ``load replace`` or ``load merge``.
  - ``discard``: discards the changes before they were committed.
  - ``rollback``: rollbacks the changes after they have been committed.

NAPALM getters script
---------------------

A ``NAPALM getters`` script is a list of getters which output is displayed in the logs.

.. image:: /_static/automation/scripts/napalm_getters_script.png
   :alt: NAPALM getters script
   :align: center

.. note:: just like with the ``NAPALM configuration`` scripts, the NAPALM driver used by eNMS is the one configured in the "Operating System" property of a node. The NAPALM drivers name must be respected: ``ios, iosxr, nxos, junos, eos``.

Ansible playbook script
-----------------------

An ``Ansible playbook`` script sends an ansible playbook to the devices.
The playbook file must be placed in the ``eNMS/playbooks`` folder, along with the Ansible configuration file (``ansible.cfg``).
To create an ``Ansible playbook`` script, simply enter the name of the playbook (example: ``the_playbook.yml``) in the ``Playbook name`` field of the form.

.. image:: /_static/automation/scripts/ansible_playbook_script.png
   :alt: Ansible script
   :align: center

Custom script
-------------

eNMS also gives you the option to create your own script. Once created, a custom script is automatically added to the web interface and can be used like any other script.
To create a custom script, add a new python file in ``eNMS/source/scripts/custom_scripts`` and use the following template:

- a function called ``job`` that contains the code of the script.
- a dictionnary called ``parameters`` that contains the parameters of your new script.

::

  def job(args):
      # Script that does nothing
      task, node, results = args
      # add your own logic here
      # results is a dictionnary that contains the logs of the script, as well
      # as a "sucess" boolean variable that indicates whether the script was
      # run successfully or not
      results[node.name] = {
          'success': True,
          'logs': 'what will be displayed in the logs'
      }

  parameters = {
      'name': 'script that does nothing',
      'node_multiprocessing': True,
      'description': 'does nothing',
      'vendor': 'none',
      'operating_system': 'all'
  }

After adding a new custom script, you must reload the application.
Custom scripts must be added to the ``eNMS/source/scripts/custom_scripts`` folder. Inside that folder, you are free to create subfolders to organize your custom scripts any way you want: eNMS will automatically detect all python files.