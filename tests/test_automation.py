from flask.testing import FlaskClient
from werkzeug.datastructures import ImmutableMultiDict

from eNMS.database.functions import fetch, fetch_all

from tests.conftest import check_pages


netmiko_ping = ImmutableMultiDict(
    [
        ("form_type", "NetmikoConfigurationService"),
        ("name", "netmiko_ping"),
        ("credentials", "user"),
        ("send_notification_method", "mail_feedback_notification"),
        ("validation_method", "text"),
        ("waiting_time", "0"),
        ("query_property_type", "ip_address"),
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
        ("shape", "box"),
    ]
)

file_transfer_service = ImmutableMultiDict(
    [
        ("form_type", "NetmikoConfigurationService"),
        ("name", "test"),
        ("credentials", "user"),
        ("send_notification_method", "mail_feedback_notification"),
        ("validation_method", "text"),
        ("waiting_time", "0"),
        ("query_property_type", "ip_address"),
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
        ("shape", "box"),
    ]
)


getters_dict = ImmutableMultiDict(
    [
        ("form_type", "NapalmGettersService"),
        ("name", "napalm_getters_service"),
        ("query_property_type", "ip_address"),
        ("credentials", "user"),
        ("send_notification_method", "mail_feedback_notification"),
        ("validation_method", "dict_equal"),
        ("description", ""),
        ("driver", "ios"),
        ("getters", "get_interfaces"),
        ("getters", "get_interfaces_ip"),
        ("getters", "get_lldp_neighbors"),
        ("shape", "box"),
    ]
)


ansible_service = ImmutableMultiDict(
    [
        ("form_type", "AnsiblePlaybookService"),
        ("name", "testttt"),
        ("query_property_type", "ip_address"),
        ("credentials", "user"),
        ("conversion_method", "text"),
        ("send_notification_method", "mail_feedback_notification"),
        ("validation_method", "text"),
        ("waiting_time", "0"),
        ("devices", "1"),
        ("devices", "2"),
        ("description", ""),
        ("vendor", ""),
        ("operating_system", ""),
        ("playbook_path", "test.yml"),
        ("arguments", "--ask-vault"),
        ("shape", "box"),
    ]
)


@check_pages("table/service")
def test_base_services(user_client: FlaskClient) -> None:
    number_of_services = len(fetch_all("Service"))
    user_client.post("/update/NetmikoConfigurationService", data=netmiko_ping)
    assert len(fetch_all("NetmikoConfigurationService")) == 3
    user_client.post("/update/NetmikoFileTransferService", data=file_transfer_service)
    assert len(fetch_all("NetmikoFileTransferService")) == 1
    number_of_napalm_services = len(fetch_all("NapalmGettersService"))
    user_client.post("/update/NapalmGettersService", data=getters_dict)
    assert len(fetch_all("NapalmGettersService")) == number_of_napalm_services + 1
    user_client.post("/update/AnsiblePlaybookService", data=ansible_service)
    assert len(fetch_all("AnsiblePlaybookService")) == 1
    assert len(fetch_all("Service")) == number_of_services + 4


@check_pages("table/workflow")
def test_yaql_test_worflow(user_client: FlaskClient) -> None:
    workflow = fetch("Workflow", name="YaQL_test_worflow")
    assert workflow.run()[0]["success"]
