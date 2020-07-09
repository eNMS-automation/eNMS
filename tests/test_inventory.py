from werkzeug.datastructures import ImmutableMultiDict

from eNMS import app
from eNMS.database import db
from eNMS.setup import properties

from tests.conftest import check_pages


def define_device(number: str, description: str) -> ImmutableMultiDict:
    return ImmutableMultiDict(
        [
            ("form_type", "device"),
            ("name", f"description-{number}"),
            ("description", description),
            ("location", "paris"),
            ("vendor", "Cisco"),
            ("icon", "router"),
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
            ("name", f"{source} too {destination}"),
            ("description", "description"),
            ("location", "Los Angeles"),
            ("vendor", "Juniper"),
            ("source", source),
            ("destination", destination),
        ]
    )


@check_pages("table/device", "table/link", "view/network")
def test_manual_object_creation(user_client):
    db.delete_all("device", "link")
    for number in range(10):
        for description in ("desc1", "desc2"):
            obj_dict = define_device(number, description)
            user_client.post("/update/device", data=obj_dict)
    # devices = db.fetch_all("device")
    # for source in devices[:3]:
    #     for destination in devices[:3]:
    #         obj_dict = define_link(source.id, destination.id)
    #         user_client.post("/update/link", data=obj_dict)
    # assert len(db.fetch_all("device")) == 10
    # assert len(db.fetch_all("link")) == 9


def create_from_file(client, file: str):
    with open(app.path / "files" / "spreadsheets" / file, "rb") as f:
        data = {"form_type": "excel_import", "file": f, "replace": False}
        client.post("/import_topology", data=data)


@check_pages("table/device", "table/link", "view/network")
def test_object_creation_europe(user_client):
    create_from_file(user_client, "europe.xls")
    assert len(db.fetch_all("device")) == 33
    assert len(db.fetch_all("link")) == 49


@check_pages("table/device", "table/link", "view/network")
def test_object_creation_type(user_client):
    create_from_file(user_client, "device_counters.xls")
    assert len(db.fetch_all("device")) == 27
    assert len(db.fetch_all("link")) == 0


routers = ["router" + str(i) for i in range(5, 20)]
links = ["link" + str(i) for i in range(4, 15)]


@check_pages("table/device", "table/link", "view/network")
def test_device_deletion(user_client):
    create_from_file(user_client, "europe.xls")
    for device_name in routers:
        device = db.fetch("device", name=device_name)
        user_client.post(f"/delete_instance/device/{device.id}")
    assert len(db.fetch_all("device")) == 18
    assert len(db.fetch_all("link")) == 18


@check_pages("table/device", "table/link", "view/network")
def test_link_deletion(user_client):
    create_from_file(user_client, "europe.xls")
    for link_name in links:
        link = db.fetch("link", name=link_name)
        user_client.post(f"/delete_instance/link/{link.id}")
    assert len(db.fetch_all("device")) == 33
    assert len(db.fetch_all("link")) == 38


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
    for property in properties["filtering"]["device"]:
        if f"device_{property}_match" not in pool:
            pool[f"device_{property}_match"] = "inclusion"
    for property in properties["filtering"]["link"]:
        if f"link_{property}_match" not in pool:
            pool[f"link_{property}_match"] = "inclusion"
    return pool


@check_pages("table/device", "table/link", "view/network")
def test_pool_management(user_client):
    create_from_file(user_client, "europe.xls")
    user_client.post("/update/pool", data=create_pool(pool1))
    user_client.post("/update/pool", data=create_pool(pool2))
    p1, p2 = db.fetch("pool", name="pool1"), db.fetch("pool", name="pool2")
    assert len(p1.devices) == 21
    assert len(p1.links) == 20
    assert len(p2.devices) == 12
    assert len(p2.links) == 4
    assert len(db.fetch_all("pool")) == 11
    # user_client.post(f"/delete_instance/pool/{p1.id}")
    # user_client.post(f"/delete_instance/pool/{p2.id}")
    # assert len(db.fetch_all("pool")) == 9
