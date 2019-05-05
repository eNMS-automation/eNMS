from contextlib import contextmanager
from datetime import datetime
from flask import Flask
from logging import info
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from os import environ
from sqlalchemy.orm import Session
from simplekml import Color, Style
from string import punctuation
from typing import Any, Dict, Generator, Set
from yaml import load, BaseLoader


class Controller:

    device_subtypes: Dict[str, str] = {
        "antenna": "Antenna",
        "firewall": "Firewall",
        "host": "Host",
        "optical_switch": "Optical switch",
        "regenerator": "Regenerator",
        "router": "Router",
        "server": "Server",
        "switch": "Switch",
    }

    link_subtypes: Dict[str, str] = {
        "bgp_peering": "BGP peering",
        "etherchannel": "Etherchannel",
        "ethernet_link": "Ethernet link",
        "optical_channel": "Optical channel",
        "optical_link": "Optical link",
        "pseudowire": "Pseudowire",
    }

    link_colors: Dict[str, str] = {
        "bgp_peering": "#77ebca",
        "etherchannel": "#cf228a",
        "ethernet_link": "#0000ff",
        "optical_link": "#d4222a",
        "optical_channel": "#ff8247",
        "pseudowire": "#902bec",
    }

    NETMIKO_DRIVERS = sorted((driver, driver) for driver in CLASS_MAPPER)
    NETMIKO_SCP_DRIVERS = sorted((driver, driver) for driver in FILE_TRANSFER_MAP)
    NAPALM_DRIVERS = sorted((driver, driver) for driver in SUPPORTED_DRIVERS[1:])

    def __init__(self):
        self.USE_SYSLOG = int(environ.get("USE_SYSLOG", False))
        self.USE_TACACS = int(environ.get("USE_TACACS", False))
        self.USE_LDAP = int(environ.get("USE_LDAP", False))
        self.USE_VAULT = int(environ.get("USE_VAULT", False))
        self.load_custom_properties()
        if self.USE_SYSLOG:
            self.configure_syslog_server()

    def init_app(self, app: Flask, session: Session):
        self.app = app
        self.session = session
        self.create_google_earth_styles()

    def configure_syslog_server(self) -> None:
        self.server = SyslogServer(
            environ.get("SYSLOG_ADDR", "0.0.0.0"), int(environ.get("SYSLOG_PORT", 514))
        )
        self.server.start()

    def allowed_file(self, name: str, allowed_modules: Set[str]) -> bool:
        allowed_syntax = "." in name
        allowed_extension = name.rsplit(".", 1)[1].lower() in allowed_modules
        return allowed_syntax and allowed_extension

    def create_google_earth_styles(self):
        self.google_earth_styles = {}
        for subtype in self.device_subtypes:
            point_style = Style()
            point_style.labelstyle.color = Color.blue
            path_icon = f"{self.app.path}/eNMS/views/static/images/2D/{subtype}.gif"
            point_style.iconstyle.icon.href = path_icon
            self.google_earth_styles[subtype] = point_style
        for subtype in self.link_subtypes:
            line_style = Style()
            color = self.link_colors[subtype]
            kml_color = "#ff" + color[-2:] + color[3:5] + color[1:3]
            line_style.linestyle.color = kml_color
            self.google_earth_styles[subtype] = line_style

    def get_time(self):
        return str(datetime.now()).replace("-", "+")

    def load_custom_properties(self) -> dict:
        filepath = environ.get("PATH_CUSTOM_PROPERTIES")
        if not filepath:
            self.custom_properties = {}
        else:
            with open(filepath, "r") as properties:
                self.custom_properties = load(properties, Loader=BaseLoader)

    @contextmanager
    def session_scope(self) -> Generator:
        session = self.session()  # type: ignore
        try:
            yield session
            session.commit()
        except Exception as e:
            info(str(e))
            session.rollback()
            raise e
        finally:
            self.session.remove()

    def str_dict(self, input: Any, depth: int = 0) -> str:
        tab = "\t" * depth
        if isinstance(input, list):
            result = "\n"
            for element in input:
                result += f"{tab}- {self.str_dict(element, depth + 1)}\n"
            return result
        elif isinstance(input, dict):
            result = ""
            for key, value in input.items():
                result += f"\n{tab}{key}: {self.str_dict(value, depth + 1)}"
            return result
        else:
            return str(input)

    def strip_all(self, input: str) -> str:
        return input.translate(str.maketrans("", "", f"{punctuation} "))


controller = Controller()
