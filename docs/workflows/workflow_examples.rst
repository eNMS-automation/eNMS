=================
Workflow Examples
=================

Configure and decommission a VRF with Netmiko
--------------------------------------------

This workflow is made of 4 services:
  - netmiko_create_vrf_TEST: uses Netmiko to configure ``ip vrf TEST`` on an IOS router.
  - netmiko_check_vrf_TEST: uses Netmiko to validate that ``TEST`` is in the output of ``show ip vrf``
  - netmiko_create_vrf_TEST: uses Netmiko to decommission with the command ``no ip vrf TEST``.