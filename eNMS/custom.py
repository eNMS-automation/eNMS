from re import sub
from warnings import warn

try:
    from ldap3 import Connection
except ImportError as exc:
    warn(f"Couldn't import ldap3 module({exc})")

from eNMS.environment import env
from eNMS.variables import vs


class CustomApp:
    def ldap_authentication(self, user, name, password):
        if not hasattr(env, "ldap_server"):
            env.log("error", "LDAP authentication failed: no server configured")
            return False
        user = f"uid={name},dc=example,dc=com"
        success = Connection(env.ldap_server, user=user, password=password).bind()
        return {"name": name, "is_admin": True} if success else False

    def tacacs_authentication(self, user, name, password):
        if not hasattr(env, "tacacs_client"):
            env.log("error", "TACACS+ authentication failed: no server configured")
            return False
        success = env.tacacs_client.authenticate(name, password).valid
        return {"name": name, "is_admin": True} if success else False

    def parse_configuration_property(self, device, property, value=None):
        if not value:
            value = getattr(device, property)
        if device.operating_system == "eos" and property == "configuration":
            value = sub(r"(username.*secret) (.*)", "\g<1> ********", value)
        return value


vs.custom = CustomApp()
