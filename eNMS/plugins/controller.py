from ldap3 import Connection


class CustomController:
    def get_ldap_user(self, name, password):
        if not hasattr(self, "ldap_server"):
            self.ldap_server = Server(environ.get("LDAP_SERVER"))
        user = f"uid={name},dc=example,dc=com"
        success = Connection(self.ldap_server, user=user, password=password).bind()
        return {"group": "admin", "name": name} if success else False

    def process_form_data(self, **data):
        return data["router_id"] * 2
