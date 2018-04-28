=========
Workflows
=========

A workflow is a directed graph which nodes are scripts.

Each script in eNMS returns a boolean value:
- ``True`` if it ran successfully.
- ``False`` otherwise.

There are two types of edge in a workflow: ``success edge`` and ``failure edge``.
The ``success edge`` indicates where to move in the graph if the source script was executed with success, while the ``failure edge`` does the same thing in case of failure.

Workflows are created and managed from the :guilabel:`workflows/workflow_management` page. 

A first example
***************

Let's consider a workflow made of four scripts:
    - ``configure-bgp``, a ``NAPALM configuration`` script that configures a BGP neighbor.
    - ``NAPALM Commit``, that commits the changes with NAPALM.
    - ``validate-bgp``, a ``Netmiko validation`` script that checks that the neighbor appears in the ``show ip bgp neighbors`` command.
    - ``NAPALM Rollback``, that rollbacks the changes with NAPALM.

The workflow below uses these four scripts together to configure a new BGP neighbor and rollbacks in case of problem.

.. image:: /_static/automation/workflows/first_example.png
   :alt: A first example
   :align: center

The green color of ``configure-bgp`` indicates that this is the beginning of the workflow (the first script to be executed).

If ``configure-bgp`` is a success (it returns the boolean value ``True``, the ``success edge`` will be used, and the ``NAPALM Commit`` script will be executed.

If ``NAPALM Commit`` runs successfully, ``validate-bgp`` will run and check that the neighbor was properly configured.

If ``validate-bgp`` is a success, the workflow will stop here as there is no ``success edge`` starting from ``validate-bgp``. On the other hand, if it fails, the workflow will go on using the ``failure edge`` and the configuration will be rolled back with NAPALM.

Creation of a workflow
**********************

In the :guilabel:`workflows/workflow_management` page, click on the button ``Add a new workflow`` and fill the workflow creation form.
The new workflow will be automatically added to the table of worflows.

.. image:: /_static/automation/workflows/workflow_creation.png
   :alt: Workflow creation
   :align: center

Clicking on the ``Manage`` button in the table of workflows to open the ``Workflow builder``.

Workflow builder
****************

.. image:: /_static/automation/workflows/workflow_builder.png
   :alt: Workflow builder
   :align: center

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

Select ``configurebgp`` and click on the ``Set as start`` button to tell eNMS that this is where the workflow begins.

The workflow is done and ready to be executed:

.. image:: /_static/automation/workflows/example5.png
   :alt: Workflow builder
   :align: center
