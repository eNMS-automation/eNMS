Transfer a one or multiple files to/from the eNMS server to the device using
either SFTP or SCP.

![Generic Filetransfer Service](../../_static/automation/service_types/generic_filetransfer.png)

!!! note

    This service supports variable substitution in the source and destination file input fields,
    as well as the credentials fields, of its configuration form.

Configuration parameters for creating this service instance:

- `Direction`- Get or Put the file from/to the target device's
  filesystem.
- `Protocol`- Use SCP or SFTP to perform the transfer.
- `Source file`- For Get, source file is the path-plus-filename on the
  device to retrieve to the eNMS server. For Put, source file is the
  path-plus-filename on the eNMS server to send to the device.
- `Destination file`- For Get, destination file is the
  path-plus-filename on the eNMS server to store the file to. For Put,
  destination file is the path-plus-filename on the device to store
  the file to.
- `Missing Host Key Policy`- If checked, auto-add the host key policy
  on the ssh connection.
- `Load Known Host Keys`- If checked, load host keys on the eNMS server
  before attempting the connection.
- `Source file includes glob pattern (Put Direction only)`- Flag
  indicates that for Put Direction transfers only, the above Source
  file field contains a [Glob pattern match](https://en.wikipedia.org/wiki/Glob_(programming))
  for selecting multiple files for transport. When Globbing is used, the
  Destination file directory should only contain a destination directory,
  because the source file names will be re-used at the destination.
- `Max Transfer Size`- This is that maximum packet size that will be
  used during transfer. This may adversely impact transfer times.
- `Window Size`- This is the requested window size during transfer.
  This may adversely impact transfer times.
- `Timeout`- How long to wait for the connection to be established.
- `Credentials`- Select between:
    - `Device Credentials`- The application will select the most appropriate credential
      object for each device. If there are multiple credentials available, the 
      `Type of Credential` and `Priority` properties become a tiebreaker.
    - `Named Credentials`- Allows users to reference a specific credential for all targets. Selecting this 
      option requires additional selections below.
    - `Custom Credentials`- Allows users to store a credential against this service. Selecting this 
      option requires additional selections below.
      
!!! Advice

    `Named Credentials` selections will persist through duplicating a service, unlike `Custom Credentials`. 
    [For details on creating a `Named Credential` take a look at this page.](../../administration/credentials.md) 

- `Named Credential`- Select from a list of user created credential objects. 
- `Custom Username`- User provided username, stored against this service.
- `Custom Password`- User provided password, stored against this service


    
    
