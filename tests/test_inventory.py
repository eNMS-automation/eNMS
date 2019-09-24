from werkzeug.datastructures import ImmutableMultiDict

from eNMS import app
from eNMS.database.functions import delete_all, fetch, fetch_all
from eNMS.properties.objects import (
    device_icons,
    pool_link_properties,
    pool_device_properties,
)

from tests.conftest import check_pages


def define_device(icon: str, description: str) -> ImmutableMultiDict:
    return ImmutableMultiDict(
        [
            ("form_type", "device"),
            ("name", icon + description),
            ("description", description),
            ("location", "paris"),
            ("vendor", "Cisco"),
            ("icon", icon),
            ("ip_address", icon + description),
            ("operating_system", "IOS"),
            ("os_version", "1.4.4.2"),
            ("longitude", "12"),
            ("latitude", "14"),
            ("enable_password", "enable_password"),
        ]
    )


def define_link(source: int, destination: int) -> ImmutableMultiDict:
    return ImmutableMultiDict(
        [
            ("form_type", "link"),
            ("name", f"{source} to {destination}"),
            ("description", "description"),
            ("location", "Los Angeles"),
            ("vendor", "Juniper"),
            ("source", source),
            ("destination", destination),
        ]
    )


@check_pages("table/device", "table/link", "view/network")
def test_manual_object_creation(user_client):
    delete_all("device", "Link")
    for icon in device_icons:
        for description in ("desc1", "desc2"):
            obj_dict = define_device(icon, description)
            user_client.post("/update/device", data=obj_dict)
    devices = fetch_all("device")
    for source in devices[:3]:
        for destination in devices[:3]:
            obj_dict = define_link(source.id, destination.id)
            user_client.post("/update/link", data=obj_dict)
    assert len(fetch_all("device")) == 16
    assert len(fetch_all("Link")) == 9


def create_from_file(client, file: str):
    with open(app.path / "projects" / "spreadsheets" / file, "rb") as f:
        data = {"form_type": "excel_import", "file": f, "replace": False}
        client.post("/import_topology", data=data)


@check_pages("table/device", "table/link", "view/network")
def test_object_creation_europe(user_client):
    create_from_file(user_client, "europe.xls")
    assert len(fetch_all("device")) == 33
    assert len(fetch_all("Link")) == 49


@check_pages("table/device", "table/link", "view/network")
def test_object_creation_type(user_client):
    create_from_file(user_client, "device_counters.xls")
    assert len(fetch_all("device")) == 27
    assert len(fetch_all("Link")) == 0


routers = ["router" + str(i) for i in range(5, 20)]
links = ["link" + str(i) for i in range(4, 15)]


@check_pages("table/device", "table/link", "view/network")
def test_device_deletion(user_client):
    create_from_file(user_client, "europe.xls")
    for device_name in routers:
        device = fetch("device", name=device_name)
        user_client.post(f"/delete_instance/device/{device.id}")
    assert len(fetch_all("device")) == 18
    assert len(fetch_all("Link")) == 18


@check_pages("table/device", "table/link", "view/network")
def test_link_deletion(user_client):
    create_from_file(user_client, "europe.xls")
    for link_name in links:
        link = fetch("Link", name=link_name)
        user_client.post(f"/delete_instance/link/{link.id}")
    assert len(fetch_all("device")) == 33
    assert len(fetch_all("Link")) == 38


pool1 = {
    "form_type": "pool",
    "name": "pool1",
    "operator": "all",
    "device_location": "france|spain",
    "device_location_match": "regex",
    "link_name": "link[1|2].",
    "link_name_match": "regex",
}

pool2 = {
    "form_type": "pool",
    "name": "pool2",
    "operator": "all",
    "device_location": "france",
    "link_name": "l.*k\\S3",
    "link_name_match": "regex",
}


def create_pool(pool: dict) -> dict:
    for property in pool_device_properties:
        if f"device_{property}_match" not in pool:
            pool[f"device_{property}_match"] = "inclusion"
    for property in pool_link_properties:
        if f"link_{property}_match" not in pool:
            pool[f"link_{property}_match"] = "inclusion"
    return pool


@check_pages("table/device", "table/link", "view/network")
def test_pool_management(user_client):
    create_from_file(user_client, "europe.xls")
    user_client.post("/update/pool", data=create_pool(pool1))
    user_client.post("/update/pool", data=create_pool(pool2))
    p1, p2 = fetch("Pool", name="pool1"), fetch("Pool", name="pool2")
    assert len(p1.devices) == 21
    assert len(p1.links) == 20
    assert len(p2.devices) == 12
    assert len(p2.links) == 4
    assert len(fetch_all("Pool")) == 9
    user_client.post(f"/delete_instance/pool/{p1.id}")
    user_client.post(f"/delete_instance/pool/{p2.id}")
    assert len(fetch_all("Pool")) == 7
