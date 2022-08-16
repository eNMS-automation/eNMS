# controller.py

# filtering function

        if (
            rbac == "read"
            and kwargs.get("type") == "configuration"
            and set(kwargs.get("form", {})) & set(vs.configuration_properties)
        ):
            rbac = "configuration"
