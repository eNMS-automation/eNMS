===================
OS upgrade workflow
===================

We consider a Cisco router with IOS ``12.4(13r)T`` and the IOS image ``c1841-spservicesk9-mz.124-8.bin``.
Let's create a workflow to upgrade to ``c1841-adventerprisek9-mz.124-8a.bin``.
The workflow will be composed of the following scripts: 

1. Version check
****************

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
*********************************

In order to transfer the new IOS image, we will use a ``Netmiko File Transfer`` script.
We place the ``c1841-adventerprisek9-mz.124-8a.bin`` in the :guilabel:`eNMS/file_transfer` folder,
and we create the file transfer script:

.. image:: /_static/automation/os_upgrade/transfer_new_image.png
   :alt: Pre-check version
   :align: center

3. Reload the device
********************

2. Delete the old IOS image
***************************

Since we have uploaded a new IOS image and moved it to the flash memory, we need some space. We erase the old IOS image from the memory: ``delete /f /r c1841-spservicesk9-mz.124-8.bin``.

We do not need to enter the configuration mode to type this command and delete the file, so we create a ``Netmiko configuration`` script of type ``"show" commands`` (and not ``configuration``).



* :guilabel:`Add script`: open a window to select which script you want to add to the workflow.
* :guilabel:`Delete selection`: delete the selected script or edge.
* :guilabel:`Set as start`: the selected script is set as the beginning of the workflow. It will be highlighted in green.
* :guilabel:`Success edge`: switch to the ``success edge`` creation mode, allowing you to draw ``success edge`` between scripts.
* :guilabel:`Failure edge`: same as ``success edge``.
* :guilabel:`Move node`: switch to the motion node, allowing you to drag the scripts on the canvas to better visualize the workflow.

.. note:: You can double-click on a script to update its properties.

Create a workflow step by step
******************************

Let's create the BGP workflow discussed in the first paragraph.

Creation of the validatebgp script
----------------------------------

In the :guilabel:`scripts/script_creation` page, we create a ``NAPALM configuration`` script to configure the BGP neighbor on the device.

Configuration:

.. image:: /_static/automation/workflows/example1.png
   :alt: Workflow builder
   :align: center

Creation of the validatebgp script
----------------------------------

In the :guilabel:`scripts/script_creation` page, we create a ``Netmiko validation`` script to check that 1.1.1.1 is indeed considered a BGP neighbor on the device.

Specifically, we are checking that the output of ``show ip bgp neighbors 1.1.1.1`` contains the line ``BGP neighbor is 1.1.1.1``.

.. image:: /_static/automation/workflows/example2.png
   :alt: Workflow builder
   :align: center

Creation of the workflow
------------------------

In the :guilabel:`workflows/workflow_management` page, click on the button ``Add a new workflow`` and fill the workflow creation form.

.. image:: /_static/automation/workflows/example3.png
   :alt: Workflow builder
   :align: center

Building the workflow
---------------------

In the :guilabel:`workflows/workflow_management` page, click on the button ``Manage`` of the newly created workflow. This opens the ``Workflow builder``.

Click on the ``Add script`` button, and add all 4 scripts: ``configurebgp``, ``validatebgp``, ``NAPALM Commit`` and ``NAPALM Rollback``.

.. image:: /_static/automation/workflows/example4.png
   :alt: Workflow builder
   :align: center

Finally, create:

- a ``success edge`` from ``configurebgp`` to ``NAPALM Commit``.
- a ``success edge`` from ``NAPALM Commit`` to ``validatebgp``.
- a ``failure edge`` from ``validatebgp`` to ``NAPALM Rollback``.

The workflow is done and ready to be executed:

.. image:: /_static/automation/workflows/example5.png
   :alt: Workflow builder
   :align: center
