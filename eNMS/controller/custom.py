from os import getenv
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
    def ldap_authentication(self, user, name, password):
        if not hasattr(self, "ldap_server"):
            self.ldap_server = Server(getenv("LDAP_ADDR"))
        user = f"uid={name},dc=example,dc=com"
        success = Connection(self.ldap_server, user=user, password=password).bind()
        return {"name": name, "is_admin": True} if success else False

    def tacacs_authentication(self, user, name, password):
        if not hasattr(self, "tacacs_client"):
            self.tacacs_client = TACACSClient(
                getenv("TACACS_ADDR"), 49, getenv("TACACS_PASSWORD")
            )
        success = self.tacacs_client.authenticate(name, password).valid
        return {"name": name, "is_admin": True} if success else False
