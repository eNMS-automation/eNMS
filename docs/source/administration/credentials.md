# Credentials

Credentials are used when connecting to a device.  Permissions for device 
access (via an `Access`) are separate from permission to use a `Credential`;
both are required for connection to a device.  `Credential` permissions are
defined directly on the `Credential` and do not involve an `Access`.

Device credentials are stored in either a Vault or in the database
if no Vault is configured. For a production environment, a Hashicorp Vault is recommended. 

![Credentials](../_static/administration/credentials.png)

**Name**: The `Credential` name.

**Description**: Credential documentation.

**Role**: Read and write, or read only

**Subtype**: Choose between `Username / Password` or `SSH Key`.

**Devices**: Pool of devices which will have access to these credentials

**Users**: Pool of users which will have access to these credentials

**Priority**: When a user has access to multiple credentials for a device,
the credential with the highest priority is chosen.

**Username**: The username for both `Username / Password` and `SSH Key` connections.

**Password**: The password for subtype `Username / Password` credentials.

**Private Key**: The SSH private key for subtype `SSH Key` credentials.

**'Enable' Password**: Used by Netmiko based services when Enable mode is
selected and a password is required.  This is not related to device
connection, but is included on the credential for Vault storage.