/*
global
action: false
alertify: false
call: false
L: false
serializeForm: false
showFilteringPanel: false
showPoolView: false
showTypePanel: false
viewType: false
WE: false
*/

const layers = {
  osm: "http://{s}.tile.osm.org/{z}/{x}/{y}.png",
  gm: "http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga",
  nasa: "http://tileserver.maptiler.com/nasa/{z}/{x}/{y}.jpg",
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

call("/get/parameters/1", function(parameters) {
  markerType = parameters.default_marker;
  if (viewType == "3D") {
    map = WE.map("map", { sky: true, atmosphere: true });
    layer = WE.tileLayer(layers["gm"]);
    layer.addTo(map);
  } else {
    map = L.map("map", { preferCanvas: true }).setView(
      [parameters.default_latitude, parameters.default_longitude],
      parameters.default_zoom_level
    );
    layer = L.tileLayer(layers["osm"]);
    map.addLayer(layer);
  }

  map.on("click", function(e) {
    selectedObject = null;
  });

  map.on("contextmenu", function() {
    if (!selectedObject) {
      $(".menu").hide();
      $(".geo-menu").show();
    }
  });

  updateView();

});

for (const [key, value] of Object.entries(iconSizes)) {
  window[`icon_${key}`] = L.icon({
    iconUrl: `../static/images/2D/${key}.gif`,
    iconSize: value,
    iconAnchor: [9, 6],
    popupAnchor: [8, -5],
  });
}

const routerIcon = window["icon_router"];

L.PolylineClusterable = L.Polyline.extend({
  _originalInitialize: L.Polyline.prototype.initialize,
  initialize: function(bounds, options) {
    this._originalInitialize(bounds, options);
    this._latlng = this.getBounds().getCenter();
  },
  getLatLng: function() {
    return this._latlng;
  },
  setLatLng: function() {},
});

// eslint-disable-next-line
function switchView(newView) {
  deleteAll();
  
  if (viewType == "2DC") {
    map.addLayer(markers);
  }
}

// eslint-disable-next-line
function switchLayer(layer) {
  if (viewType !== "3D") {
    map.removeLayer(layer2D);
    layer2D = L.tileLayer(layers[layer]);
    map.addLayer(layer2D);
  } else {
    layer3D.removeFrom(earth);
    layer3D = WE.tileLayer(layers[layer]);
    layer3D.addTo(earth);
  }
  $(".dropdown-submenu a.menu-layer")
    .next("ul")
    .toggle();
}

// eslint-disable-next-line
function changeMarker(type) {
  markerType = type;
  switchView(viewType);
}

// eslint-disable-next-line
function createNode2d(node, nodeType) {
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
  return marker;
}

// eslint-disable-next-line
function createNode3d(node, nodeType) {
  let marker;
  if (markerType == "Image") {
    marker = WE.marker(
      [node.latitude, node.longitude],
      `../static/images/3D/${nodeType == "device" ? "router" : "site"}.gif`,
      15,
      10
    ).addTo(earth);
  } else {
    marker = WE.marker([node.latitude, node.longitude]).addTo(earth);
  }
  marker.on("mouseover", function(e) {
    $("#name-box").text(node.name);
    $("#name-box").show();
  });
  marker.on("mouseout", function(e) {
    $("#name-box").hide();
  });
  return marker;
}

// eslint-disable-next-line
function createNode(node, nodeType) {
  if (!node.latitude && !node.longitude) return;
  let marker;
  if (viewType == "3D") {
    marker = createNode3d(node, nodeType);
  } else {
    marker = createNode2d(node, nodeType);
  }
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
  marker.addTo(map);
}

// eslint-disable-next-line
function createLink2d(link) {
  let pointA = new L.LatLng(link.source_latitude, link.source_longitude);
  let pointB = new L.LatLng(
    link.destination_latitude,
    link.destination_longitude
  );
  const pointList = [pointA, pointB];
  const polyline = new L.PolylineClusterable(pointList, {
    color: link.color,
    weight: 3,
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
    selectedObject = this.link; // eslint-disable-line no-undef
  });
  polyline.bindTooltip(link.name, {
    permanent: false,
  });
  if (viewType == "2D") {
    polyline.addTo(map);
  } else {
    markers.addLayer(polyline);
  }
}

// eslint-disable-next-line
function createLink3d(link) {
  const color = link.color.trimRight();
  const polygonSD = WE.polygon(
    [
      [link.source_latitude, link.source_longitude],
      [link.destination_latitude, link.destination_longitude],
      [link.source_latitude, link.source_longitude],
    ],
    { color: color, opacity: 20 }
  ).addTo(earth);
  const polygonDS = WE.polygon(
    [
      [link.destination_latitude, link.destination_longitude],
      [link.source_latitude, link.source_longitude],
      [link.destination_latitude, link.destination_longitude],
    ],
    { color: color, opacity: 20 }
  ).addTo(earth);
  polygonSD.link_id = polygonDS.link_id = link.id;
  polylinesArray.push(polygonSD, polygonDS);
}

// eslint-disable-next-line
function createLink(link) {
  if (viewType == "2D" || viewType == "2DC") {
    createLink2d(link);
  } else {
    createLink3d(link);
  }
}

function deleteAllDevices() {
  for (let i = 0; i < markersArray.length; i++) {
    if (viewType == "2D") {
      markersArray[i].removeFrom(map);
    } else if (viewType == "3D") {
      markersArray[i].removeFrom(earth);
    } else {
      markers.removeLayer(markersArray[i]);
    }
  }
  markersArray = [];
}

function deleteAllLinks() {
  for (let i = 0; i < polylinesArray.length; i++) {
    if (viewType == "2D") {
      polylinesArray[i].removeFrom(map);
    } else if (viewType == "2DC") {
      markers.removeLayer(polylinesArray[i]);
    } else {
      try {
        polylinesArray[i].destroy();
      } catch (err) {
        // catch
      }
    }
  }
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
  NASA: () => switchLayer("nasa"),
  "Display sites": () => switchView(viewType),
  "2D": () => switchView("2D"),
  "Clustered 2D": () => switchView("2DC"),
  "3D": () => switchView("3D"),
  Image: () => changeMarker("Image"),
  Circle: () => changeMarker("Circle"),
  "Circle Marker": () => changeMarker("Circle Marker"),
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
function updateView() {
  deleteAll();
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
}

// eslint-disable-next-line
function filter(type) {
  $.ajax({
    type: "POST",
    url: `/view_filtering/${type}`,
    data: { form: serializeForm(`#${type}_filtering-form`) },
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

// eslint-disable-next-line
function showViewFilteringPanel(type) {
  showFilteringPanel(`${type}_filtering`);
}
