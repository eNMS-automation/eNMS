=============
Release Notes
=============

Version 3.18
------------

- Add Operational Data mechanism
- Removed Clusterized and 3D View
- Changed configuration to be a .json file instead of env variables
- Removed Custom config and PATH_CUSTOM_CONFIG
- Remove Configuration comparison mechanism
- Display the results of a workflow as a tree
- Change the mechanism to add a service to a workflow to be a tree
- Add the forward and backward control to the service managemet table.
- Duplicate button at workflow level to duplicate any workflow as top-level workflow
- Update to the operational data backup service to include rancid-like prefixes
- Add new "run method" property to define how a service is running (once per device, or once for all devices),
  and the equivalent property for workflow: run device by device, or service by service.
- Replace endtime with "duration" in the results and run table
- Fix bug infinite loop when adding a workflow to itself
- New "run method" option for services: : 
  - once per device
  - once for all devices
- New "run method" option for workflow
  - run device by device
  - service by service with workflow targets
  - service by service with service targets
