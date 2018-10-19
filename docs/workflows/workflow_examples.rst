=================
Workflow Examples
=================

Configure and decommission a VRF with Netmiko
--------------------------------------------

This workflow is made of 4 services:
  - netmiko_create_vrf_TEST: uses Netmiko to configure ``ip vrf TEST`` on an IOS router.

    .. image:: /_static/workflows/netmiko_workflow/create_vrf.png
      :alt: Create VRF TEST
      :align: center

  - netmiko_check_vrf_TEST: uses Netmiko to validate that ``TEST`` is in the output of ``show ip vrf``.

    .. image:: /_static/workflows/netmiko_workflow/check_vrf.png
      :alt: Validate VRF TEST
      :align: center

  - netmiko_create_vrf_TEST: uses Netmiko to decommission with the command ``no ip vrf TEST``.

    .. image:: /_static/workflows/netmiko_workflow/delete_vrf.png
      :alt: Delete VRF TEST
      :align: center

  - netmiko_check_vrf_TEST: uses Netmiko to validate that ``TEST`` is NOT in the output of ``show ip vrf``. In order to perform that check, we must use a regular expression: we check that the ouput of ``show ip vrf`` is matched by the regular expression ``^((?!TEST).)*$``.

    .. image:: /_static/workflows/netmiko_workflow/check_no_vrf.png
      :alt: Validate there is no VRF TEST
      :align: center

Configure and decommission a VRF with Napalm
--------------------------------------------

This workflow performs the same action as the previous one (create and delete a VRF called ``TEST``, and validate each step), except it uses Napalm to create and decommission the VRF.

The creation step is handled by Napalm ``load_merge`` function while the VRF deletion relies on Napalm ``rollback`` function.

.. image:: /_static/workflows/other_workflows/napalm_workflow.png
   :alt: Napalm workflow
   :align: center
