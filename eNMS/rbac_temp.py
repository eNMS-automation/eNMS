# inventory.py

# Object class

    @classmethod
    def rbac_filter(cls, query, mode, user):
        if cls.__tablename__ == "node":
            return query
        pool_alias = aliased(vs.models["pool"])
        return (
            query.join(cls.pools)
            .join(vs.models["access"], vs.models["pool"].access)
            .join(pool_alias, vs.models["access"].user_pools)
            .join(vs.models["user"], pool_alias.users)
            .filter(vs.models["access"].access_type.contains(mode))
            .filter(vs.models["user"].name == user.name)
            .group_by(cls.id)
        )

# Pool class

    @classmethod
    def rbac_filter(cls, query, *_):
        return query.filter(cls.admin_only == false())


# automation.py

# Service class

    @classmethod
    def rbac_filter(cls, query, mode, user):
        pool_alias = aliased(vs.models["pool"])
        query = (
            query.join(cls.pools)
            .join(vs.models["access"], vs.models["pool"].access)
            .join(pool_alias, vs.models["access"].user_pools)
            .join(vs.models["user"], pool_alias.users)
            .filter(vs.models["access"].access_type.contains(mode))
            .filter(vs.models["user"].name == user.name)
            .filter(cls.admin_only == false())
            .group_by(cls.id)
        )
        originals_alias = aliased(vs.models["service"])
        owners_alias = aliased(vs.models["user"])
        if mode in ("edit", "run"):
            services_with_no_access_configured = {
                service.id
                for service in db.session.query(cls.id).filter(
                    ~cls.originals.any(cls.owners_access.contains(mode))
                )
            }
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

# Run class

    @classmethod
    def rbac_filter(cls, query, mode, user):
        service_alias = aliased(vs.models["service"])
        pool_alias = aliased(vs.models["pool"])
        services = (
            service.id
            for service in db.session.query(vs.models["user"])
            .join(pool_alias, vs.models["user"].pools)
            .join(vs.models["access"], pool_alias.access_users)
            .join(vs.models["pool"], vs.models["access"].access_pools)
            .join(service_alias, vs.models["pool"].services)
            .filter(vs.models["user"].name == user.name)
            .filter(vs.models["access"].access_type.contains(mode))
            .filter(service_alias.admin_only == false())
            .with_entities(service_alias.id)
            .all()
        )
        return query.join(cls.service).filter(vs.models["service"].id.in_(services))

# Task class

    @classmethod
    def rbac_filter(cls, query, mode, user):
        pool_alias = aliased(vs.models["pool"])
        return (
            query.join(cls.service)
            .join(vs.models["pool"], vs.models["service"].pools)
            .join(vs.models["access"], vs.models["pool"].access)
            .join(pool_alias, vs.models["access"].user_pools)
            .join(vs.models["user"], pool_alias.users)
            .filter(vs.models["access"].access_type.contains(mode))
            .filter(vs.models["user"].name == user.name)
            .filter(cls.admin_only == false())
        )

# workflow.py

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

# access types

  access_type: "['Read', 'Configuration', 'Edit', 'Run', 'Schedule', 'Connect', 'Use\
    \ as target']"

# base.py update function

        if not kwargs.get("update_pools") or not self.pool_model:
            return
        rbac_pools_kwargs = {
            "rbac": None,
            "manually_defined": False,
            "admin_only": True,
        }
        for pool in db.fetch_all("pool", **rbac_pools_kwargs):
            match = pool.match_instance(self)
            if match and self not in getattr(pool, f"{self.class_type}s"):
                getattr(pool, f"{self.class_type}s").append(self)
            if self in getattr(pool, f"{self.class_type}s") and not match:
                getattr(pool, f"{self.class_type}s").remove(self)