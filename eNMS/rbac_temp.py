
def query(self, model, rbac="read", username=None, properties=None):
    ...
    if rbac and model != "user":
        user = current_user or self.fetch("user", name=username or "admin")
        if user.is_authenticated and not user.is_admin:
            if model in vs.rbac["advanced"]["admin_models"].get(rbac, []):
                raise self.rbac_error
            if (
                rbac == "read"
                and vs.rbac["advanced"]["deactivate_rbac_on_read"]
                and model != "pool"
            ):
                return query
            query = vs.models[model].rbac_filter(query, rbac, user)

# base.py

    @classmethod
    def rbac_filter(cls, query, *_):
        return query

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

    def update(self, **kwargs):
        old_users = set(self.users)
        super().update(**kwargs)
        if not kwargs.get("import_mechanism", False):
            self.compute_pool()
            for user in set(self.users) | old_users:
                user.update_rbac()

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

# administration.py

# User class

    if not kwargs.get("import_mechanism", False):
        self.update_rbac()

    def update_rbac(self):
        if self.is_admin:
            return
        db.session.commit()
        user_access = (
            db.session.query(vs.models["access"])
            .join(vs.models["pool"], vs.models["access"].user_pools)
            .join(vs.models["user"], vs.models["pool"].users)
            .filter(vs.models["user"].name == self.name)
            .all()
        )
        for property in vs.rbac:
            if property in ("advanced", "all_pages"):
                continue
            access_value = (getattr(access, property) for access in user_access)
            setattr(self, property, list(set(chain.from_iterable(access_value))))

# controller.py

# filtering function

        if (
            rbac == "read"
            and kwargs.get("type") == "configuration"
            and set(kwargs.get("form", {})) & set(vs.configuration_properties)
        ):
            rbac = "configuration"