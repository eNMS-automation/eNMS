from os import environ
from warnings import warn

try:
    from ldap3 import Connection, Server
except ImportError as exc:
    warn(f"Couldn't import ldap3 module ({exc})")
try:
    from tacacs_plus.client import TACACSClient
except ImportError as exc:
    warn(f"Couldn't import tacacs_plus module ({exc})")


class CustomController:
    def ldap_authentication(self, name, password):
        if not hasattr(self, "ldap_server"):
            self.ldap_server = Server(environ.get("LDAP_SERVER"))
        user = f"uid={name},dc=example,dc=com"
        success = Connection(self.ldap_server, user=user, password=password).bind()
        return {"group": "admin", "name": name} if success else False

    def tacacs_authentication(self, name, password):
        if not hasattr(self, "tacacs_client"):
            TACACSClient(environ.get("TACACS_ADDR"), 49, environ.get("TACACS_PASSWORD"))
        success = self.tacacs_server.authenticate(name, password).valid
        return {"group": "admin", "name": name} if success else False

    def process_form_data(self, **data):
        return data["router_id"] * 2
