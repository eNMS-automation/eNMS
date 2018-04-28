==========
OS upgrade
==========

We consider a Cisco router with IOS ``12.4(13r)T`` and the IOS image ``c1841-spservicesk9-mz.124-8.bin``.
Let's create a workflow to upgrade to ``c1841-adventerprisek9-mz.124-8a.bin``.

Creation of the scripts
***********************

The workflow will be composed of the following scripts: 

1. Version check
----------------

We use a ``Netmiko validation`` script to make sure that the current IOS image used by the current is the one we want to update.
In other words, we check that:

- The output of ``show version`` contains ``System image file is "flash:c1841-spservicesk9-mz.124-8.bin"``.
- The output of ``dir`` contains ``c1841-spservicesk9-mz.124-8.bin``.

If either of this condition fails, the ``Netmiko validation`` script will fail, and the workflow will stop.

We create the following script ``version-check-before-reload`` from the :guilabel:`script/script_creation` page.

.. image:: /_static/automation/os_upgrade/version_check_before_reload.png
   :alt: Pre-check version
   :align: center

2. Transferring the new IOS image
---------------------------------

In order to transfer the new IOS image, we will use a ``Netmiko File Transfer`` script.
We place the ``c1841-adventerprisek9-mz.124-8a.bin`` in the :guilabel:`eNMS/file_transfer` folder,
and we create the file transfer script:

.. image:: /_static/automation/os_upgrade/transfer_new_image.png
   :alt: Transfer new IOS image
   :align: center

3. Preconfigure the router for the upgrade
------------------------------------------

We need to upgrade the configuration register to ``0x2102``, and tell the router to boot from the IOS image that we've uploaded in the last step.

We create a ``Netmiko configuration`` script of type ``configuration`` with the following commands:

.. image:: /_static/automation/os_upgrade/preconfiguration.png
   :alt: Preconfiguration
   :align: center

4. Save and reload
------------------

We use a ``Netmiko configuration`` of type ``"show" commands`` to save the latest changes and reload the device.

Each script has a ``Waiting time`` parameter (seconds) that tells eNMS how much time it must wait before proceeding to the next script in the workflow.

After sending the script, we have to wait a bit for the device to reload and be available again: we set the ``waiting time`` of the script to ``120`` (2 minutes).

.. image:: /_static/automation/os_upgrade/save_and_reload.png
   :alt: Save configuration and reload the device
   :align: center

5. Post-reload version check
----------------------------

We create a ``Netmiko validation`` script similar to the one used in the first step to check that the IOS image used by the router is indeed the new one.

.. image:: /_static/automation/os_upgrade/version_check_after_reload.png
   :alt: Post-check version
   :align: center

6. Delete the old IOS image
---------------------------

Since we have uploaded a new IOS image and moved it to the flash memory, we need some space. We erase the old IOS image from the memory: ``delete /f /r c1841-spservicesk9-mz.124-8.bin``.

We do not need to enter the configuration mode to type this command and delete the file, so we create a ``Netmiko configuration`` script of type ``"show" commands`` (and not ``configuration``).

.. image:: /_static/automation/os_upgrade/delete_old_image.png
   :alt: Delete the old IOS image
   :align: center

Creation of the workflow
************************

1. Creation form
----------------

In the :guilabel:`workflows/workflow_management` page, click on the button ``Add a new workflow`` and fill the workflow creation form.

.. image:: /_static/automation/os_upgrade/workflow_creation.png
   :alt: Create workflow
   :align: center

2. Building the workflow
------------------------

In the :guilabel:`workflows/workflow_management` page, click on the button ``Manage`` of the newly created workflow. This opens the ``Workflow builder``.

Click on the ``Add script`` button, and add all 6 scripts:

- ``version-check-before-reload``
- ``preconfiguration``
- ``transfer-new-image``
- ``save-and-reload``
- ``version-check-after-reload``
- ``delete-old-image``

Between each consecutive pair of scripts, we create a success edge, and we set ``version-check-before-reload`` as the beginning of the workflow.

The workflow is done and ready to be executed:

.. image:: /_static/automation/os_upgrade/reload_workflow.png
   :alt: Reload workflow
   :align: center
