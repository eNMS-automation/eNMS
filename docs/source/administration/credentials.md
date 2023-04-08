# Credentials

This section explains how to manage username and password details for logging into a device. 

In a typical installation, most credentials are hidden using the `Admin Only` check box described below. However, when a user creates a credential, it becomes available under `Step 2` of most services as a `Named Credential`. 

!!! Advice
    These are the required fields when creating a `Named Credential`:

    - **Name**: Unique identification for referencing the credential
    - **Role**: Read and write, or read only.
    - **Subtype**: Choose between `Username / Password` or `SSH Key`.
    - **Groups**: Groups of users which will have access to these credentials.
    - **Username**: The username for both `Username / Password` and `SSH Key` connections.
    - **Password or Private Key**: If `Subtype` from above is `Username / Password`, the field becomes `Password`. If `Subtype` from above is `SSH Key`, the field becomes `Private Key`. 

<br/>
<h4>Credential Details</h4> 

![Credentials](../_static/administration/credentials.png)

* **Name**: Unique identification for referencing the credential
* **Creator**: Auto Populated field based on the user who built the credential
* **Admin Only**: An override of `Access Control`, which prevents non-admin users from viewing or editing the credential object. However, this does not determine who can use the credential, which is handled by `Users` below. 
* **Description**: Text field for storing notes  

* **Role**: Read and write, or read only.
* **Subtype**: Choose between `Username / Password` or `SSH Key`.
* **Devices**: Pool of devices which will have access to these credentials.
* **Groups**: Groups of users which will have access to these credentials.
* **Priority**: When a user has access to multiple credentials for a device, the credential with the highest priority is chosen.
* **Username**: The username for both `Username / Password` and `SSH Key` connections.
* **Password or Private Key**: If `Subtype` from above is `Username / Password`, the field becomes `Password`. If `Subtype` from above is `SSH Key`, the field becomes `Private Key`.  
* **'Enable' Password**: Used by Netmiko based services when Enable mode is selected and a password is required.  This is not related to device connection, but is included on the credential for Vault storage.

<br/>
<h4>Access Control Details</h4> 
- [Details on Access Control for this object](overview.md) 
  

<br/>
<h4>Vault Details</h4> 
A vault is typically used to store a device's credentials, for a production environment, Hashicorp Vault is recommended. Credentials may also be stored in the main database. 
