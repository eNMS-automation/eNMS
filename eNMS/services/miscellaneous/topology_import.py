from pynetbox import api as netbox_api
from requests import get as http_get
from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField, PasswordField

from eNMS.database.dialect import Column, SmallString
from eNMS.database.functions import factory
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SelectField, StringField
from eNMS.models.automation import Service


class TopologyImportService(Service):

    __tablename__ = "topology_import_service"
    pretty_name = "Topology Import"
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)
    netbox_address = Column(SmallString)
    netbox_token = Column(SmallString)
    opennms_address = Column(SmallString)
    opennms_devices = Column(SmallString)
    opennms_login = Column(SmallString)
    opennms_password = Column(SmallString)
    librenms_address = Column(SmallString)
    librenms_token = Column(SmallString)

    import_type = Column(SmallString)

    __mapper_args__ = {"polymorphic_identity": "topology_import_service"}

    def job(self, run, payload):
        getattr(self, f"query_{self.import_type}")()
        return {"success": True}

    def query_netbox(self):
        nb = netbox_api(self.netbox_address, self.netbox_token)
        for device in nb.dcim.devices.all():
            device_ip = device.primary_ip4 or device.primary_ip6
            factory(
                "device",
                **{
                    "name": device.name,
                    "ip_address": str(device_ip).split("/")[0],
                    "subtype": str(device.device_role),
                    "model": str(device.device_type),
                    "location": str(device.site),
                    "vendor": str(device.device_type.manufacturer),
                    "operating_system": str(device.platform),
                    "longitude": str(nb.dcim.sites.get(name=device.site).longitude),
                    "latitude": str(nb.dcim.sites.get(name=device.site).latitude),
                },
            )

    def query_opennms(self):
        json_devices = http_get(
            self.opennms_devices,
            headers={"Accept": "application/json"},
            auth=(self.opennms_login, self.opennms_password),
        ).json()["node"]
        devices = {
            device["id"]: {
                "name": device.get("label", device["id"]),
                "description": device["assetRecord"].get("description", ""),
                "location": device["assetRecord"].get("building", ""),
                "vendor": device["assetRecord"].get("manufacturer", ""),
                "model": device["assetRecord"].get("modelNumber", ""),
                "operating_system": device.get("operatingSystem", ""),
                "os_version": device["assetRecord"].get("sysDescription", ""),
                "longitude": device["assetRecord"].get("longitude", 0.0),
                "latitude": device["assetRecord"].get("latitude", 0.0),
            }
            for device in json_devices
        }
        for device in list(devices):
            link = http_get(
                f"{self.opennms_address}/nodes/{device}/ipinterfaces",
                headers={"Accept": "application/json"},
                auth=(self.opennms_login, self.opennms_password),
            ).json()
            for interface in link["ipInterface"]:
                if interface["snmpPrimary"] == "P":
                    devices[device]["ip_address"] = interface["ipAddress"]
                    factory("device", **devices[device])

    def query_librenms(self):
        devices = http_get(
            f"{self.librenms_address}/api/v0/devices",
            headers={"X-Auth-Token": self.librenms_token},
        ).json()["devices"]
        for device in devices:
            factory(
                "device",
                **{
                    "name": device["hostname"],
                    "ip_address": device["ip"] or device["hostname"],
                    "model": device["hardware"],
                    "operating_system": device["os"],
                    "os_version": device["version"],
                    "location": device["location"],
                    "longitude": device["lng"],
                    "latitude": device["lat"],
                },
            )


class TopologyImportForm(ServiceForm):
    form_type = HiddenField(default="topology_import_service")
    import_type = SelectField(
        choices=(
            ("librenms", "LibreNMS"),
            ("netbox", "Netbox"),
            ("opennms", "OpenNMS"),
        )
    )
    netbox_address = StringField(default="http://0.0.0.0:8000")
    netbox_token = PasswordField()
    opennms_address = StringField()
    opennms_devices = StringField()
    opennms_login = StringField()
    opennms_password = PasswordField()
    librenms_address = StringField(default="http://librenms.example.com")
    librenms_token = PasswordField()
    groups = {
        "Type of Import": {"commands": ["import_type"], "default": "expanded"},
        "Netbox": {
            "commands": ["netbox_address", "netbox_token"],
            "default": "expanded",
        },
        "OpenNMS": {
            "commands": [
                "opennms_address",
                "opennms_devices",
                "opennms_login",
                "opennms_password",
            ],
            "default": "expanded",
        },
        "LibreNMS": {
            "commands": ["librenms_address", "librenms_token"],
            "default": "expanded",
        },
    }
