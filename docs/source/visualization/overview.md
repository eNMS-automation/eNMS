---
title: Network Visualization
---

# Overview

If network data has been created, it can be displayed on a geographical
map or in the Network Builder topology view. All devices with longitude and
latitude data can be displayed on a map at their exact location along with
links connecting devices. There are two rendering options available for
network visualization, 2D or 3D.  The rendering type is set in the
`visualization.json` file.  For more information about setting this
configuration option please refer to the `Installation` documentation.

## Common Visualization Controls

There are several components at the top center of the display that
can be used to customize what data is shown.  These components are common to 
all network visualization options.

![Main Controls](../_static/visualization/controls_1.png)

- Dropdown list - Displays all pools containing devices and links. Selecting
one causes all devices and links defined in the selected pool to be displayed
- Buttons (From left to right)
    - Edit Pool: Change criteria for what entities will be included in the
      defined pool.  Refer to the `Inventory / Pools` section of documentation
      for information on pool creation.
    - Device Filtering: Opens a dialog to provide criteria for selecting a
      subset of pool devices currently displayed.  Enter criteria, close the
      dialog and hit the Refresh button to update the display.
    - Link Filtering: Opens a dialog to provide criteria for selecting a subset
      of links currently displayed.  Enter criteria, close the dialog and hit
      the Refresh button to update the display.
    - Refresh: This button is used to refresh the display and is required 
      to apply any filtering changes
    - Clear Search - Removes all filtering criteria and refreshes the map
    - Run Service: Opens a dialog box to select and run a service on all
      devices currently displayed on the map
    - Previous View: View previously selected pool/filtering data on the map
    - Next View: View pool/filtering data on map that is more recent than data
      currently being displayed. This option is only available if you have
      clicked the Previous View button.

