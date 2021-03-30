from os import getenv
from re import sub
from warnings import warn

try:
    from ldap3 import Connection, Server
except ImportError as exc:
    warn(f"Couldn't import ldap3 module ({exc})")

try:
    from tacacs_plus.client import TACACSClient
except ImportError as exc:
    warn(f"Couldn't import tacacs_plus module ({exc})")


class CustomApp:
    def __init__(self, app):
        self.app = app

    def pre_init(self):
        pass

    def post_init(self):
        pass

    def ldap_authentication(self, user, name, password):
        if not hasattr(self.app, "ldap_server"):
            self.app.ldap_server = Server(getenv("LDAP_ADDR"))
        user = f"uid={name},dc=example,dc=com"
        success = Connection(self.app.ldap_server, user=user, password=password).bind()
        return {"name": name, "is_admin": True} if success else False

    def tacacs_authentication(self, user, name, password):
        if not hasattr(self.app, "tacacs_client"):
            self.app.tacacs_client = TACACSClient(
                getenv("TACACS_ADDR"), 49, getenv("TACACS_PASSWORD")
            )
        success = self.app.tacacs_client.authenticate(name, password).valid
        return {"name": name, "is_admin": True} if success else False

    def parse_configuration_property(self, device, property, value=None):
        if not value:
            value = getattr(device, property)
        if device.operating_system == "eos" and property == "configuration":
            value = sub(r"(username.*secret) (.*)", "\g<1> ********", value)
        return value
