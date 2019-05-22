from eNMS.controller.administration import AdministrationController
from eNMS.controller.automation import AutomationController
from eNMS.controller.default import DefaultController
from eNMS.controller.examples import ExamplesController
from eNMS.controller.inventory import InventoryController


class Controller(
    AdministrationController,
    AutomationController,
    DefaultController,
    ExamplesController,
    InventoryController,
):

    valid_post_endpoints = [
        "add_edge",
        "add_jobs_to_workflow",
        "calendar_init",
        "clear_results",
        "clear_configurations",
        "connection",
        "counters",
        "count_models",
        "database_helpers",
        "delete_edge",
        "delete_instance",
        "delete_node",
        "duplicate_workflow",
        "export_to_google_earth",
        "export_topology",
        "get",
        "get_all",
        "get_cluster_status",
        "get_configurations",
        "get_configuration_diff",
        "get_device_logs",
        "get_git_content",
        "get_job_logs",
        "get_job_results",
        "get_results_diff",
        "get_view_topology",
        "import_topology",
        "migration_export",
        "migration_import",
        "query_netbox",
        "query_librenms",
        "query_opennms",
        "reset_status",
        "run_job",
        "save_device_jobs",
        "save_parameters",
        "save_pool_objects",
        "save_positions",
        "scan_cluster",
        "scheduler",
        "task_action",
        "topology_import",
        "update",
        "update_parameters",
        "update_pools",
        "view_filtering",
    ]

    log_severity = {"error": error, "info": info, "warning": warning}

    def __getattr__(self, property: str) -> Any:
        return self.config[property]

    def __init__(self) -> None:
        self.custom_properties = self.load_custom_properties()
        self.config = self.load_config()
        self.configure_scheduler()
        if self.use_tacacs:
            self.configure_tacacs_client()
        if self.use_ldap:
            self.configure_ldap_client()
        if self.use_vault:
            self.configure_vault_client()
        if self.use_syslog:
            self.configure_syslog_server()

    def initialize_app(self, app: Flask) -> None:
        self.app = app
        self.path = app.path
        self.create_google_earth_styles()
        self.configure_logs()

    def initialize_database(self):
        self.create_default_parameters()
        self.create_default()
        if self.create_examples:
            self.create_examples()

    def create_default_parameters(self) -> None:
        parameters = Session.query(models["Parameters"]).one_or_none()
        if not parameters:
            parameters = models["Parameters"]()
            parameters.update(
                **{
                    property: self.config[property]
                    for property in model_properties["Parameters"]
                    if property in self.config
                }
            )
            Session.add(parameters)
            Session.commit()
        else:
            self.config.update(parameters.get_properties())

    def configure_logs(self) -> None:
        basicConfig(
            level=getattr(import_module("logging"), self.enms_log_level),
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%m-%d-%Y %H:%M:%S",
            handlers=[
                RotatingFileHandler(
                    self.app.path / "logs" / "app_logs" / "enms.log",
                    maxBytes=20_000_000,
                    backupCount=10,
                ),
                StreamHandler(),
            ],
        )

    def load_services(self) -> None:
        path_services = [self.app.path / "eNMS" / "services"]
        if self.custom_services_path:
            path_services.append(Path(self.custom_services_path))
        for path in path_services:
            for file in path.glob("**/*.py"):
                if "init" in str(file):
                    continue
                if not self.create_examples and "examples" in str(file):
                    continue
                spec = spec_from_file_location(str(file).split("/")[-1][:-3], str(file))
                assert isinstance(spec.loader, Loader)
                module = module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                except InvalidRequestError as e:
                    error(f"Error loading custom service '{file}' ({str(e)})")

    def configure_ldap_client(self) -> None:
        self.ldap_client = Server(self.ldap_server, get_info=ALL)

    def configure_tacacs_client(self) -> None:
        self.tacacs_client = TACACSClient(self.tacacs_addr, 49, self.tacacs_password)

    def configure_vault_client(self) -> None:
        self.vault_client = VaultClient()
        self.vault_client.url = self.vault_addr
        self.vault_client.token = environ.get("VAULT_TOKEN")
        if self.vault_client.sys.is_sealed() and self.unseal_vault:
            keys = [environ.get(f"UNSEAL_VAULT_KEY{i}") for i in range(1, 6)]
            self.vault_client.sys.submit_unseal_keys(filter(None, keys))

    def configure_syslog_server(self) -> None:
        self.syslog_server = SyslogServer(self.syslog_addr, self.syslog_port)
        self.syslog_server.start()


controller = Controller()
