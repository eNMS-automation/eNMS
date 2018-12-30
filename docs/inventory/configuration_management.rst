========================
Configuration Management
========================

eNMS can work as a network device configuration backup tool, and replace Oxidized/Rancid.
  - Poll network elements and download configuration when it changes
  - Ability to easily view current configuration of a device in the inventory
  - Search feature for any text in any configuration
  - For a given inventory device, view differences between different versions of configurations (perhaps this would rely on the proposed git archival service for git diff?)
  - Download configuration for a device to a local text file
  - Use the ReST API support to return a specified device's configuration
  - Export all device configurations to a remote Git repository (e.g Gitlab)

Configuration
*************



.. image:: /_static/inventory/objects/object_types.png
   :alt: Different types of objects
   :align: center
