export default class Device {

  constructor (properties) {
    Object.assign(this, properties);
  }

  get test() {
    return "3";
  }

  get buttons() {
    return `
      <ul class="pagination pagination-lg" style="margin: 0px; width: 300px">
        <li>
          <button type="button" class="btn btn-info"
          onclick="showDeviceNetworkData({self.row_properties})"
          data-tooltip="Network Data"
            ><span class="glyphicon glyphicon-cog"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-info"
          onclick="showDeviceResultsPanel({self.row_properties})"
          data-tooltip="Results"
            ><span class="glyphicon glyphicon-list-alt"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-success"
          onclick="showPanel('device_connection', '{self.id}')"
          data-tooltip="Connection"
            ><span class="glyphicon glyphicon-console"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-primary"
          onclick="showTypePanel('device', '{self.id}')" data-tooltip="Edit"
            ><span class="glyphicon glyphicon-edit"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-primary"
          onclick="showTypePanel('device', '{self.id}', 'duplicate')"
          data-tooltip="Duplicate"
            ><span class="glyphicon glyphicon-duplicate"></span
          ></button>
        </li>
        <li>
          <button type="button" class="btn btn-danger"
          onclick="showDeletionPanel({self.row_properties})" data-tooltip="Delete"
            ><span class="glyphicon glyphicon-trash"></span
          ></button>
        </li>
      </ul>`
  }
}