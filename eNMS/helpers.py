from git import Repo
from git.exc import GitCommandError
from logging import info
from napalm._SUPPORTED_DRIVERS import SUPPORTED_DRIVERS
from netmiko.ssh_dispatcher import CLASS_MAPPER, FILE_TRANSFER_MAP
from pathlib import Path, PosixPath
from typing import Optional, Set
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from xlrd import open_workbook
from xlrd.biffh import XLRDError
from xlwt import Workbook

from eNMS.extensions import controller, db
from eNMS.functions import (
    delete_all,
    factory,
    fetch_all,
    serialize,
    fetch,
    get_one,
    str_dict,
)
from eNMS.properties import export_properties

NETMIKO_DRIVERS = sorted((driver, driver) for driver in CLASS_MAPPER)
NETMIKO_SCP_DRIVERS = sorted((driver, driver) for driver in FILE_TRANSFER_MAP)
NAPALM_DRIVERS = sorted((driver, driver) for driver in SUPPORTED_DRIVERS[1:])


def allowed_file(name: str, allowed_extensions: Set[str]) -> bool:
    allowed_syntax = "." in name
    allowed_extension = name.rsplit(".", 1)[1].lower() in allowed_extensions
    return allowed_syntax and allowed_extension


def object_import(request: dict, file: FileStorage) -> str:
    if request["replace"]:
        delete_all("Device")
    result = "Topology successfully imported."
    if allowed_file(secure_filename(file.filename), {"xls", "xlsx"}):
        book = open_workbook(file_contents=file.read())
        for obj_type in ("Device", "Link"):
            try:
                sheet = book.sheet_by_name(obj_type)
            except XLRDError:
                continue
            properties = sheet.row_values(0)
            for row_index in range(1, sheet.nrows):
                prop = dict(zip(properties, sheet.row_values(row_index)))
                prop["dont_update_pools"] = True
                try:
                    factory(obj_type, **prop).serialized
                except Exception as e:
                    info(f"{str(prop)} could not be imported ({str(e)})")
                    result = "Partial import (see logs)."
            db.session.commit()
    for pool in fetch_all("Pool"):
        pool.compute_pool()
    db.session.commit()
    info("Inventory import: Done.")
    return result


def object_export(request: dict, path_app: PosixPath) -> bool:
    workbook = Workbook()
    filename = request["export_filename"]
    if "." not in filename:
        filename += ".xls"
    for obj_type in ("Device", "Link"):
        sheet = workbook.add_sheet(obj_type)
        for index, property in enumerate(export_properties[obj_type]):
            sheet.write(0, index, property)
            for obj_index, obj in enumerate(serialize(obj_type), 1):
                sheet.write(obj_index, index, obj[property])
    workbook.save(path_app / "projects" / filename)
    return True


def scheduler_job(
    job_id: int,
    aps_job_id: Optional[str] = None,
    targets: Optional[Set["Device"]] = None,
    payload: Optional[dict] = None,
) -> None:
    with controller.app.app_context():
        task = fetch("Task", creation_time=aps_job_id)
        job = fetch("Job", id=job_id)
        if targets:
            targets = {fetch("Device", id=device_id) for device_id in targets}
        results, now = job.try_run(targets=targets, payload=payload)
        parameters = get_one("Parameters")
        if job.push_to_git and parameters.git_automation:
            path_git_folder = Path.cwd() / "git" / "automation"
            with open(path_git_folder / job.name, "w") as file:
                file.write(str_dict(results))
            repo = Repo(str(path_git_folder))
            try:
                repo.git.add(A=True)
                repo.git.commit(m=f"Automatic commit ({job.name})")
            except GitCommandError:
                pass
            repo.remotes.origin.push()
        if task and not task.frequency:
            task.is_active = False
        db.session.commit()
