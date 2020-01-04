from os import environ
from pynetbox import api as netbox_api
from sqlalchemy import ForeignKey, Integer
from wtforms import HiddenField, SelectField

from eNMS import app
from eNMS.database.dialect import Column
from eNMS.forms.automation import ServiceForm
from eNMS.models.automation import Service


class TopologyImportService(Service):

    __tablename__ = "topology_import"
    pretty_name = "Topology Import"
    driver = Column(SmallString)
    id = Column(Integer, ForeignKey("service.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "topology_import"}

    def job(self, run, payload):
        getattr(self, f"query_{self.import_type}")()
        return {"success": True}

    def query_netbox(self):
        nb = netbox_api(
            app.config["netbox"]["address"], token=environ.get("NETBOX_TOKEN")
        )
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
        login = app.config["opennms"]["login"]
        password = environ.get("OPENNMS_PASSWORD")
        Session.commit()
        json_devices = http_get(
            app.config["opennms"]["devices"],
            headers={"Accept": "application/json"},
            auth=(login, password),
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
                f"{app.config['opennms']['address']}/nodes/{device}/ipinterfaces",
                headers={"Accept": "application/json"},
                auth=(login, password),
            ).json()
            for interface in link["ipInterface"]:
                if interface["snmpPrimary"] == "P":
                    devices[device]["ip_address"] = interface["ipAddress"]
                    factory("device", **devices[device])


class TopologyImportForm(ServiceForm):
    form_type = HiddenField(default="topology_import")
    import_type = SelectField(
        choices=(
            ("netbox", "Netbox"),
            ("opennms", "OpenNMS"),
        )
    )
