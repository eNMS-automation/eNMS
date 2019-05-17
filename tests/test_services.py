from flask.testing import FlaskClient
from werkzeug.datastructures import ImmutableMultiDict

from eNMS.database.functions import fetch_all

from tests.test_base import check_pages


netmiko_ping = ImmutableMultiDict(
    [
        ("form_type", "service"),
        ("name", "netmiko_ping"),
        ("waiting_time", "0"),
        ("devices", "1"),
        ("devices", "2"),
        ("description", ""),
        ("vendor", ""),
        ("operating_system", ""),
        ("content_type", "simple"),
        ("content", "ping 1.1.1.1"),
        ("netmiko_type", "show_commands"),
        ("driver", "cisco_xr_ssh"),
        ("global_delay_factor", "1.0"),
    ]
)

file_transfer_service = ImmutableMultiDict(
    [
        ("form_type", "service"),
        ("name", "test"),
        ("waiting_time", "0"),
        ("devices", "1"),
        ("devices", "2"),
        ("description", ""),
        ("vendor", ""),
        ("operating_system", ""),
        ("driver", "cisco_ios"),
        ("source_file", "path/to/source"),
        ("dest_file", "path/to/destination"),
        ("file_system", "flash:"),
        ("direction", "put"),
    ]
)


@check_pages("table-service")
def test_base_services(user_client: FlaskClient) -> None:
    user_client.post("/update-NetmikoConfigurationService", data=netmiko_ping)
    assert len(fetch_all("NetmikoConfigurationService")) == 3
    assert len(fetch_all("Service")) == 26
    user_client.post("/update-NetmikoFileTransferService", data=file_transfer_service)
    assert len(fetch_all("NetmikoFileTransferService")) == 1
    assert len(fetch_all("Service")) == 27


getters_dict = ImmutableMultiDict(
    [
        ("form_type", "service"),
        ("name", "napalm_getters_service"),
        ("description", ""),
        ("driver", "ios"),
        ("getters", "get_interfaces"),
        ("getters", "get_interfaces_ip"),
        ("getters", "get_lldp_neighbors"),
    ]
)


@check_pages("table-service")
def test_getters_service(user_client: FlaskClient) -> None:
    user_client.post("/update-NapalmGettersService", data=getters_dict)
    assert len(fetch_all("NapalmGettersService")) == 5


ansible_service = ImmutableMultiDict(
    [
        ("form_type", "service"),
        ("name", "testttt"),
        ("waiting_time", "0"),
        ("devices", "1"),
        ("devices", "2"),
        ("description", ""),
        ("vendor", ""),
        ("operating_system", ""),
        ("playbook_path", "test.yml"),
        ("arguments", "--ask-vault"),
    ]
)


@check_pages("table-service")
def test_ansible_services(user_client: FlaskClient) -> None:
    user_client.post("/update-AnsiblePlaybookService", data=ansible_service)
    assert len(fetch_all("AnsiblePlaybookService")) == 1
    assert len(fetch_all("Service")) == 26
