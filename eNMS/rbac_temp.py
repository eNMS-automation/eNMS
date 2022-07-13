
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
