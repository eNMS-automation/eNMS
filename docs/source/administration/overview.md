# Access

## Overview

In this section, the word instance refers any of the following objects: `device`, `service`, `credential`, `link`, `network`, and `pool`. Each of
these instances has an `Access Control` section that allows the owner(s) to determine which `Groups` are allowed to use
the instance. `Access Control` also allows the owner(s) to determine the type of access allowed. 

[Groups are easily synonymous with teams, click for details on how to create and manage.](groups.md) 


<br/>
<h4>Service</h4> 

![service_access_control](../_static/administration/access_control_service.png)

When viewing or editing a service `Step 1`, contains an `Access Control` panel that has the following properties: 

* **Owners**: Users allowed to modify this `Access Control` panel
* **Read**: `Groups` allowed to view this instance
* **Edit**: `Groups` allowed to modify this instance
* **Run**: `Groups` allowed to use this service
* **Restrict to Owners** 
> * **Edit**: When selected, prevents anyone other than those listed in the `Owners` section above from modifying this service. 
> * **Run**: When selected, prevents anyone other than those listed in the `Owners` section above from using this service.

<br/>
<h4>Device</h4>

![device_access_control](../_static/administration/access_control_device.png)

When viewing or editing a device, there are two selectable tabs near the top: `Common Properties` and `Access Control`. The
`Access Control` tab has the following properties: 

* **Owners**: Users allowed to modify this `Access Control` instance
* **Read**: `Groups` allowed to view this instance.
* **Configuration**: `Groups` allowed to view the configuration attribute of a device instance. 
* **Edit` - `Groups** allowed to modify this instance.
* **Connect via SSH**: `Groups` allowed to use the `Connection` or WebSSH feature found on the device table. 
* **Use as Target**: `Groups` allowed to use this device to run services. 

<br/>
<h4>Credentials, Links, Networks, Pools</h4>

![link_access_control](../_static/administration/access_control_link.png)

When viewing or editing a link, network, or pool there are two selectable tabs near the top: `Common Properties` and `Access Control`. The
`Access Control` tab has the following properties: 

* **Owners**: Users allowed to modify this `Access Control` instance
* **Read**: `Groups` allowed to view this instance
* **Edit**: `Groups` allowed to modify this instance
