
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