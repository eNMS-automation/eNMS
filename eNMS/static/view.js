/*
global
action: false
alertify: false
call: false
config: true
L: false
serializeForm: false
showDeviceNetworkData: false
showPanel: false
showPoolView: false
showTypePanel: false
viewType: false
*/

import { call } from "./base.js";

const layers = {
  osm: "http://{s}.tile.osm.org/{z}/{x}/{y}.png",
  gm: "http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga",
};

const iconSizes = {
  antenna: [18, 12],
  firewall: [18, 12],
  host: [18, 12],
  optical_switch: [18, 12],
  regenerator: [18, 12],
  router: [18, 12],
  server: [18, 12],
  switch: [18, 12],
  site: [22, 22],
};

let selectedObject;
let markersArray = [];
let polylinesArray = [];
let layer;
let markerType;
let map;
let markers = L.markerClusterGroup();
let clustered;

for (const [key, value] of Object.entries(iconSizes)) {
  window[`icon_${key}`] = L.icon({
    iconUrl: `../static/images/view/${key}.gif`,
    iconSize: value,
    iconAnchor: [9, 6],
    popupAnchor: [8, -5],
  });
}

const routerIcon = window["icon_router"];

// eslint-disable-next-line
function switchLayer(layerType) {
  map.removeLayer(layer);
  layer = L.tileLayer(layers[layerType]);
  map.addLayer(layer);
}

// eslint-disable-next-line
function changeMarker(type) {
  markerType = type;
  updateView();
}

// eslint-disable-next-line
function createNode(node, nodeType) {
  if (!node.latitude && !node.longitude) return;
  const marker =
    markerType == "Circle Marker"
      ? L.circleMarker([node.latitude, node.longitude])
      : markerType == "Circle"
      ? L.circle([node.latitude, node.longitude])
      : L.marker([node.latitude, node.longitude]);
  if (markerType == "Image") {
    marker.icon =
      nodeType === "device"
        ? (marker.icon = window[`icon_${node.icon}`] || routerIcon)
        : (marker.icon = window["icon_site"]);
    marker.setIcon(marker.icon);
  }
  marker.bindTooltip(node["name"], { permanent: false });
  marker.node_id = node.id;
  markersArray.push(marker);
  marker.on("click", function(e) {
    if (nodeType == "site") {
      showPoolView(node.id);
    } else {
      showTypePanel(nodeType, node.id);
    }
  });
  marker.on("contextmenu", function(e) {
    $(".menu").hide();
    $(`.rc-${nodeType}-menu`).show();
    selectedObject = node; // eslint-disable-line no-undef
  });
  if (clustered) {
    markers.addLayer(marker);
  } else {
    marker.addTo(map);
  }
}

// eslint-disable-next-line
function createLink(link) {
  if (clustered) return;
  let pointA = new L.LatLng(link.source_latitude, link.source_longitude);
  let pointB = new L.LatLng(
    link.destination_latitude,
    link.destination_longitude
  );
  const pointList = [pointA, pointB];
  const polyline = new L.Polyline(pointList, {
    color: link.color,
    weight: 2,
    opacity: 1,
    smoothFactor: 1,
  });
  polylinesArray.push(polyline);
  polyline.link_id = link.id;
  polyline.on("click", function(e) {
    showTypePanel("link", this.link_id);
  });
  polyline.on("contextmenu", function(e) {
    $(".menu").hide();
    $(".rc-link-menu").show();
    selectedObject = link; // eslint-disable-line no-undef
  });
  polyline.bindTooltip(link.name, {
    permanent: false,
  });
  polyline.addTo(map);
}

function deleteAllDevices() {
  for (let i = 0; i < markersArray.length; i++) {
    if (clustered) {
      markers.removeLayer(markersArray[i]);
    } else {
      markersArray[i].removeFrom(map);
    }
  }
  markersArray = [];
}

function deleteAllLinks() {
  polylinesArray.map((l) => l.removeFrom(map));
  polylinesArray = [];
}

function deleteAll() {
  deleteAllDevices();
  deleteAllLinks();
}

Object.assign(action, {
  // eslint-disable-line no-unused-vars
  "Open Street Map": () => switchLayer("osm"),
  "Google Maps": () => switchLayer("gm"),
  Image: () => changeMarker("Image"),
  Circle: () => changeMarker("Circle"),
  "Circle Marker": () => changeMarker("Circle Marker"),
  Normal: () => updateView(),
  Clustered: () => updateView(true),
});

$("body").contextMenu({
  menuSelector: "#contextMenu",
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selectedObject);
    selectedObject = null;
  },
});

// eslint-disable-next-line
function updateView(withCluster) {
  deleteAll();
  clustered = withCluster;
  if (viewType == "network") {
    call("/get_view_topology", function(topology) {
      topology.devices.map((d) => createNode(d, "device"));
      topology.links.map(createLink);
    });
  } else {
    $(".menu").hide();
    call("/get_all/pool", function(pools) {
      for (let i = 0; i < pools.length; i++) {
        if (pools[i].longitude) {
          createNode(pools[i], "site");
        }
      }
    });
    $(".geo-menu").show();
  }
  if (clustered) {
    map.addLayer(markers);
  } else {
    map.removeLayer(markers);
  }
}

// eslint-disable-next-line
function filter(type) {
  $.ajax({
    type: "POST",
    url: `/view_filtering/${type}`,
    contentType: "application/json",
    data: JSON.stringify({ form: serializeForm(`#${type}_filtering-form`) }),
    success: function(results) {
      if (type == "device") {
        deleteAllDevices();
        results.map((d) => createNode(d, "device"));
      } else {
        deleteAllLinks();
        results.map(createLink);
      }
      alertify.notify("Filter applied.", "success", 5);
    },
  });
}

Object.assign(action, {
  Properties: (o) => showTypePanel(o.icon ? "device" : "link", o.id),
  Connect: (d) => showPanel("device_connection", d.id),
  Configuration: (d) => showDeviceNetworkData(d),
});

(function() {
  markerType = config.view.marker;
  map = L.map("map", { preferCanvas: true }).setView(
    [config.view.latitude, config.view.longitude],
    config.view.zoom_level
  );
  layer = L.tileLayer(layers[config.view.tile_layer]);
  map
    .addLayer(layer)
    .on("click", function(e) {
      selectedObject = null;
    })
    .on("contextmenu", function() {
      if (!selectedObject) {
        $(".menu").hide();
        $(".geo-menu").show();
      }
    });
  updateView();
})();
