class Device {
  constructor(properties) {
    Object.assign(this, properties);
  }

  get buttons() {
    const instance = JSON.stringify(this);
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 230px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick='eNMS.showDeviceNetworkData(${instance})'
          data-tooltip="Network Data"
            ><span class="glyphicon glyphicon-cog"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="showDeviceResultsPanel(${instance})"
          data-tooltip="Results"
            ><span class="glyphicon glyphicon-list-alt"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-success"
          onclick="eNMS.showPanel('device_connection', '${this.id}')"
          data-tooltip="Connection"
            ><span class="glyphicon glyphicon-console"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.showTypePanel('device', '${
            this.id
          }')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.showTypePanel('device', '${this.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick="showDeletionPanel(${instance})" data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>`;
  }
}

class Link {
  constructor(properties) {
    Object.assign(this, properties);
  }

  get buttons() {
    const instance = JSON.stringify(this);
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 120px">
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.showTypePanel('link', '${this.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.showTypePanel('link', '${this.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick='showDeletionPanel(${instance})' data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>`;
  }
}

class Pool {
  constructor(properties) {
    Object.assign(this, properties);
  }

  get object_number() {
    return `${this.device_number} devices - ${this.link_number} links`;
  }

  get buttons() {
    const instance = JSON.stringify(this);
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 250px">
        <li>
          <button type="button" class="btn btn-sm btn-info"
          onclick="showPoolView('${this.id}')" data-tooltip="Internal View"
            ><span class="glyphicon glyphicon-eye-open"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="showPoolObjectsPanel('${this.id}')" data-tooltip="Pool Objects"
            ><span class="glyphicon glyphicon-wrench"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="updatePools('${this.id}')" data-tooltip="Update"
            ><span class="glyphicon glyphicon-refresh"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.showTypePanel('pool', '${this.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-primary"
          onclick="eNMS.showTypePanel('pool', '${this.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-sm btn-danger"
          onclick="showDeletionPanel(${instance})" data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>
    `;
  }
}

Pool.columns = [
  {data: "name", title: "Name"},
  {data: "last_modified", title: "Last modified"},
  {data: "description", title: "Description"},
  {data: "never_update", title: "Never update"},
  {data: "longitude", title: "Longitude"},
  {data: "latitude", title: "Latitude"},
  {data: "object_number", title: "Object Count"},
  {data: "buttons"},
]

Link.columns = [
  "name",
  "description",
  "subtype",
  "model",
  "location",
  "vendor",
  "source_name",
  "destination_name",
  "buttons",
];

Device.columns = [
  "name",
  "description",
  "subtype",
  "model",
  "location",
  "vendor",
  "operating_system",
  "os_version",
  "ip_address",
  "port",
  "buttons",
];

const models = {
  device: Device,
  link: Link,
  pool: Pool,
};

export default models;
