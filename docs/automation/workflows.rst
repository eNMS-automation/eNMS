=========
Workflows
=========

A workflow is a directed graph which nodes are scripts.
Each script in eNMS returns a boolean value, ``True`` if it ran successfully, ``False`` otherwise.
There are two types of edge in a workflow: ``success edge`` and ``failure edge``.
The ``success edge`` indicates where to move in the graph if the source script was executed with success, while the ``failure edge`` does the same thing in case of failure.
Workflows are created and managed from the :guilabel:`workflows/workflow_management` page. 

A first example
---------------

Let's consider a workflow made of four scripts:
    - ``configure-bgp``, a ``NAPALM configuration`` script that configures a BGP neighbor.
    - ``NAPALM Commit``, that commits the changes with NAPALM.
    - ``validate-bgp``, a ``Netmiko validation`` script that checks that the neighbor appears in the ``show ip bgp neighbors`` command.
    - ``NAPALM Rollback``, that rollbacks the changes with NAPALM.

The workflow below uses these four scripts together to configure a new BGP neighbor and rollbacks in case of problem.

.. image:: /_static/automation/workflows/first_example.png
   :alt: A first example
   :align: center

The green color of ``configure-bgp`` indicates that this is the beginning of the workflow (the first script to be executed). If ``configure-bgp`` is a success (it returns the boolean value ``True``, the ``success edge`` will be used, and the ``NAPALM Commit`` script will be executed.

If ``NAPALM Commit`` runs successfully, ``validate-bgp`` will run and check that the neighbor was properly configured. If ``validate-bgp`` is a success, the workflow will stop here as there is no ``success edge`` starting from ``validate-bgp``. On the other hand, if it fails, the workflow will go on using the ``failure edge`` and the configuration will be rolled back with NAPALM.

Creation of a workflow
----------------------

Click on the button ``Add a new workflow`` and fill the workflow creation form.
The new workflow will be automatically added to the table of worflow.

.. image:: /_static/automation/workflows/workflow_creation.png
   :alt: Workflow creation
   :align: center

Clicking on the ``Manage`` button in the table of workflows opens the ``Workflow builder``.

Workflow builder
----------------

.. image:: /_static/automation/workflows/workflow_builder.png
   :alt: Workflow builder
   :align: center

* :guilabel:`Add script`: open a window to select which script you want to add to the workflow.
* :guilabel:`Delete selection`: delete the selected script or edge.
* :guilabel:`Set as start`: the selected script is set as the beginning of the workflow. It will be highlighted in green.
* :guilabel:`Success edge`: switch to the ``success edge`` creation mode, allowing you to draw ``success edge`` between scripts.
* :guilabel:`Failure edge`: same as ``success edge``.
* :guilabel:`Move node`: switch to the motion node, allowing you to drag the scripts on the canvas to better visualize the workflow.
