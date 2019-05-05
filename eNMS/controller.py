from contextlib import contextmanager
from datetime import datetime
from flask import Flask
from logging import info
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from sqlalchemy.orm import Session
from string import punctuation
from typing import Any, Generator, Set


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

    controller.link_subtypes: Dict[str, str] = {
        "bgp_peering": "BGP peering",
        "etherchannel": "Etherchannel",
        "ethernet_link": "Ethernet link",
        "optical_channel": "Optical channel",
        "optical_link": "Optical link",
        "pseudowire": "Pseudowire",
    }

    NETMIKO_DRIVERS = sorted((driver, driver) for driver in CLASS_MAPPER)
    NETMIKO_SCP_DRIVERS = sorted((driver, driver) for driver in FILE_TRANSFER_MAP)
    NAPALM_DRIVERS = sorted((driver, driver) for driver in SUPPORTED_DRIVERS[1:])

    def init_app(self, app: Flask, session: Session):
        self.app = app
        self.session = session

    def allowed_file(self, name: str, allowed_modules: Set[str]) -> bool:
        allowed_syntax = "." in name
        allowed_extension = name.rsplit(".", 1)[1].lower() in allowed_modules
        return allowed_syntax and allowed_extension

    def get_time(self):
        return str(datetime.now()).replace("-", "+")

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
