# Users

Table of users. Depending on application configuration, the `Groups` column can be used to enhance Role Based Access 
(RBAC).

- **Username**: Identifies the user within the application

- **Description**: Display-only information regarding the user

- **Groups**: A comma separated list of arbitrary names available for matching
  a Pool.

    - RBAC manages collections of users using `Pools`.  User membership in a pool is
      based on filters and available for any User property, including `Groups`
      (See [Pools](../inventory/pools.md) for more information).

    - Pools are also used to determine levels of `Access` and available `Credentials`.

    - When a user creates a service, that user's `Groups` supply the default `Groups`
      assigned to the service; meaning users in their group also get access. 

- **Email Address**: The user's email address

- **Pools**: Clicking this provides a table of all the `Pools` in which this user
  is a member.
