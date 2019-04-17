/*
global
action: false
enterSite: false
L: false
link_colors: false
parameters: false
showTypeModal: false
subtype_sizes: false
updateView: false
WE: false
*/

const layers = {
  osm: "http://{s}.tile.osm.org/{z}/{x}/{y}.png",
  gm: "http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga",
  nasa: "http://tileserver.maptiler.com/nasa/{z}/{x}/{y}.jpg",
};

let selectedObject;
let markersArray = [];
let polylinesArray = [];
let currentView = parameters.default_view;
let dimension = currentView.substring(0, 2);
let markerType = parameters.default_marker;

const map = L.map("map", { preferCanvas: true }).setView(
  [parameters.default_latitude, parameters.default_longitude],
  parameters.default_zoom_level
);
const options = { sky: true, atmosphere: true };
const earth = WE.map("earth", options);

const osmLayer = L.tileLayer(layers["osm"]);
map.addLayer(osmLayer);
let layer2D = osmLayer;
let layer3D = WE.tileLayer(layers["gm"]);
layer3D.addTo(earth);
let markers = L.markerClusterGroup();

if (currentView == "3D") {
  $("#map").css("visibility", "hidden");
} else {
  $("#earth").css("visibility", "hidden");
}

for (const [key, value] of Object.entries(subtype_sizes)) {
  window[`icon_${key}`] = L.icon({
    iconUrl: `static/images/2D/${key}.gif`,
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

/**
 * Switch currentView.
 * @param {newView} newView - 2D, 2DC (clustered) or 3D.
 */
// eslint-disable-next-line
function switchView(newView) {
  deleteAll();
  const newDimension = newView.substring(0, 2);
  if (dimension != newDimension) {
    $("#map,#earth").css("visibility", "visible");
    $(".flip-container").toggleClass("hover");
    setTimeout(function() {
      if (newDimension == "3D") {
        $("#map").css("visibility", "hidden");
      } else {
        $("#earth").css("visibility", "hidden");
      }
    }, 1600);
  } else {
    $(`#${newDimension == "2D" ? "map" : "earth"}`).css(
      "visibility",
      "visible"
    );
  }
  dimension = newDimension;
  currentView = newView;
  $(`#btn-${currentView}`).hide();
  if (currentView == "2D") {
    $("#btn-2DC,#btn-3D").show();
  } else if (currentView == "2DC") {
    $("#btn-2D,#btn-3D").show();
  } else {
    $("#btn-2D,#btn-2DC").show();
  }
  updateView();
  if (currentView == "2DC") {
    map.addLayer(markers);
  }
}

/**
 * Change the tile layer.
 * @param {layer} layer - tile layer.
 */
// eslint-disable-next-line
function switchLayer(layer) {
  if (currentView !== "3D") {
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

/**
 * Change the type of marker.
 * @param {type} type - Type of marker.
 */
// eslint-disable-next-line
function changeMarker(type) {
  markerType = type;
  switchView(currentView);
}

/**
 * Create a node (device or site).
 * @param {node} node - Device or Pool.
 * @param {nodeType} nodeType - Device or Pool.
 */
// eslint-disable-next-line
function createNode(node, nodeType) {
  let marker = null;
  if (currentView == "2D" || currentView == "2DC") {
    if (markerType == "Circle Marker") {
      marker = L.circleMarker([node.latitude, node.longitude]);
    } else if (markerType == "Circle") {
      marker = L.circle([node.latitude, node.longitude]);
    } else {
      marker = L.marker([node.latitude, node.longitude]);
      if (nodeType === "device") {
        marker.icon = window[`icon_${node.subtype}`] || routerIcon;
      } else {
        marker.icon = window["icon_site"];
      }
      marker.setIcon(marker.icon);
    }
    marker.bindTooltip(node["name"], { permanent: false });
  } else {
    if (markerType == "Image") {
      marker = WE.marker(
        [node.latitude, node.longitude],
        `static/images/3D/${nodeType == "device" ? "router" : "site"}.gif`,
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
  }
  marker.node_id = node.id;
  markersArray.push(marker);
  marker.on("click", function(e) {
    if (nodeType == "site") {
      enterSite(node.id);
    } else {
      showTypeModal(nodeType, node.id);
    }
  });
  marker.on("contextmenu", function(e) {
    $(".menu").hide();
    $(`.rc-${nodeType}-menu`).show();
    selectedObject = node.id; // eslint-disable-line no-undef
  });
  if (currentView == "2D") {
    marker.addTo(map);
  } else if (currentView == "2DC") {
    markers.addLayer(marker);
  }
}

/**
 * Create a link.
 * @param {link} link - Link.
 */
// eslint-disable-next-line
function createLink(link) {
  if (currentView == "2D" || currentView == "2DC") {
    let pointA = new L.LatLng(link.source_latitude, link.source_longitude);
    let pointB = new L.LatLng(
      link.destination_latitude,
      link.destination_longitude
    );
    const pointList = [pointA, pointB];
    const polyline = new L.PolylineClusterable(pointList, {
      color: link_colors[link.subtype],
      weight: 3,
      opacity: 1,
      smoothFactor: 1,
    });
    polylinesArray.push(polyline);
    polyline.link_id = link.id;
    polyline.on("click", function(e) {
      showTypeModal("link", this.link_id);
    });
    polyline.on("contextmenu", function(e) {
      $(".menu").hide();
      $(".rc-link-menu").show();
      selectedObject = this.link_id; // eslint-disable-line no-undef
    });
    polyline.bindTooltip(link.name, {
      permanent: false,
    });
    if (currentView == "2D") {
      polyline.addTo(map);
    } else {
      markers.addLayer(polyline);
    }
  } else {
    const color = link.color;
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
}

/**
 * Delete all devices and links on the map.
 */
function deleteAll() {
  for (let i = 0; i < markersArray.length; i++) {
    if (currentView == "2D") {
      markersArray[i].removeFrom(map);
    } else if (currentView == "3D") {
      markersArray[i].removeFrom(earth);
    } else {
      markers.removeLayer(markersArray[i]);
    }
  }
  for (let i = 0; i < polylinesArray.length; i++) {
    if (currentView == "2D") {
      polylinesArray[i].removeFrom(map);
    } else if (currentView == "2DC") {
      markers.removeLayer(polylinesArray[i]);
    } else {
      try {
        polylinesArray[i].destroy();
      } catch (err) {
        // catch
      }
    }
  }
  markersArray = [];
  polylinesArray = [];
}

map.on("click", function(e) {
  selectedObject = null;
});

earth.on("click", function(e) {
  $(".menu").hide();
  $(".geo-menu").show();
});

map.on("contextmenu", function() {
  if (!selectedObject) {
    $(".menu").hide();
    $(".geo-menu").show();
  }
});

$(".dropdown-submenu a.menu-submenu").on("click", function(e) {
  $(this)
    .next("ul")
    .toggle();
  e.stopPropagation();
  e.preventDefault();
});

$("body").contextMenu({
  menuSelector: "#contextMenu",
  menuSelected: function(invokedOn, selectedMenu) {
    const row = selectedMenu.text();
    action[row](selectedObject);
    selectedObject = null;
  },
});
