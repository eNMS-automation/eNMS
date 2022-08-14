# automation.py

# Service class

    @classmethod
    def rbac_filter(cls, query, mode, user):
        originals_alias = aliased(vs.models["service"])
        owners_alias = aliased(vs.models["user"])
        if mode in ("edit", "run"):
            services_allowed_for_user = {
                service.id
                for service in db.session.query(cls.id)
                .join(originals_alias, cls.originals)
                .join(owners_alias, originals_alias.owners)
                .filter(owners_alias.name == user.name)
            }
            shared_services = {
                service.id
                for service in db.session.query(cls.id).filter(cls.shared == true())
            }
            query = query.filter(
                cls.id.in_(
                    services_with_no_access_configured
                    | services_allowed_for_user
                    | shared_services
                )
            )
        return query

    @classmethod
    def rbac_filter(cls, query, mode, user):
        if mode == "edit":
            originals_alias = aliased(vs.models["service"])
            pool_alias = aliased(vs.models["pool"])
            user_alias = aliased(vs.models["user"])
            query = (
                query.join(cls.workflow)
                .join(vs.models["pool"], vs.models["service"].pools)
                .join(vs.models["access"], vs.models["pool"].access)
                .join(pool_alias, vs.models["access"].user_pools)
                .join(user_alias, pool_alias.users)
                .filter(vs.models["access"].access_type.contains(mode))
                .filter(user_alias.name == user.name)
            )
            query = (
                query.join(cls.workflow)
                .join(originals_alias, vs.models["service"].originals)
                .filter(~originals_alias.owners_access.contains(mode))
                .union(
                    query.join(vs.models["user"], originals_alias.owners).filter(
                        vs.models["user"].name == user.name
                    )
                )
            )
        return query

# controller.py

# filtering function

        if (
            rbac == "read"
            and kwargs.get("type") == "configuration"
            and set(kwargs.get("form", {})) & set(vs.configuration_properties)
        ):
            rbac = "configuration"
