from re import sub
from uuid import uuid4
from warnings import warn

try:
    from ldap3 import Server, Connection, ALL
except ImportError as exc:
    warn(f"Couldn't import ldap3 module({exc})")

from eNMS.environment import env
from eNMS.variables import vs


class CustomApp:
    def ldap_authentication(self, user_dn, name, password):
        if not hasattr(env, "ldap_server"):
            env.log("error", "LDAP authentication failed: no server configured")
            return False
        try:
            conn = Connection(env.ldap_server, user=(env.ldap_binduser + "@" + env.ldap_userdn),
                              password=env.ldap_bindpassword, auto_bind=True)
            conn.search(env.ldap_basedn, '(sAMAccountName={})'.format(name))
            if len(conn.entries) == 1:
                user_dn = conn.entries[0].entry_dn
                conn = Connection(env.ldap_server, user=user_dn, password=password, auto_bind=True)
                if conn.bind():
                    print('worked')
                    return {"name": name, "is_admin": True} if conn else False
                else:
                    return False
            else:
                return False
        except Exception as e:
            print("Error:", e)
            return False

    def tacacs_authentication(self, user, name, password):
        if not hasattr(env, "tacacs_client"):
            env.log("error", "TACACS+ authentication failed: no server configured")
            return False
        success = env.tacacs_client.authenticate(name, password).valid
        return {"name": name, "is_admin": True} if success else False

    def parse_configuration_property(self, device, property, value=None):
        if not value:
            value = getattr(device, property)
        if device.operating_system == "EOS" and property == "configuration":
            value = sub(r"(username.*secret) (.*)", "\g<1> ********", value)
        return value

    def generate_uuid(self):
        return str(uuid4())

    def run_post_processing(self, run, run_result):
        if run.is_main_run:
            env.log(
                "info",
                (
                    f"RUNTIME {run_result['runtime']} - USER {run.creator} -"
                    f"SERVICE '{run_result['properties']['scoped_name']}' - "
                    f"Completed in {run_result['duration']}"
                ),
            )


vs.custom = CustomApp()
