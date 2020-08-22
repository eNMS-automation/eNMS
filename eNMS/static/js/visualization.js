/*
global
action: false
Cesium: false
ForceGraph3D: false
jsPanel: false
L: false
page: false
SpriteText: false
theme: false
THREE: false
vis: false
visualization: false
*/

import {
  call,
  configureNamespace,
  createTooltip,
  notify,
  serializeForm,
  showTypePanel,
} from "./base.js";
import { showConnectionPanel, showDeviceData } from "./inventory.js";

const layers = {
  osm: "http://{s}.tile.osm.org/{z}/{x}/{y}.png",
  gm: "http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga",
};

let graph;
let dimension;
let selectedObject;
let markersArray = [];
let polylinesArray = [];
let layer;
let markerType;
let map;
let markerGroup;
let clustered;
let selected;
let logicalDevices = {};
let logicalLinks = {};
let geographicalDevices = {};
let geographicalLinks = {};
let routerIcon;
let viewer;
let handler;
let polylines;
let labels;

function initGeographicalFramework() {
  dimension = visualization.geographical.default;
  if (dimension == "2D") {
    init2dGeographicalFramework();
  } else {
    init3dGeographicalFramework();
  }
}

function init2dGeographicalFramework() {
  const settings2d = visualization.geographical._2D;
  markerType = settings2d.marker;
  markerGroup = L.markerClusterGroup();
  map = L.map("map", { preferCanvas: true }).setView(
    [settings2d.latitude, settings2d.longitude],
    settings2d.zoom_level
  );
  layer = L.tileLayer(layers[settings2d.tile_layer]);
  map
    .addLayer(layer)
    .on("click", function (e) {
      selectedObject = null;
    })
    .on("contextmenu", function () {
      if (!selectedObject) {
        $(".menu").hide();
        $(".geo-menu").show();
      }
    });
  for (const [key, value] of Object.entries(settings2d.icons)) {
    window[`icon_${key}`] = L.icon({
      iconUrl: `../static/img/view/3D/${key}.gif`,
      iconSize: value,
      iconAnchor: [9, 6],
      popupAnchor: [8, -5],
    });
  }
  routerIcon = window["icon_router"];
}

function init3dGeographicalFramework() {
  polylines = new Cesium.PolylineCollection();
  let providerViewModels = Object.entries(visualization.geographical._3D.layers).map(
    function ([name, properties]) {
      const iconUrl = `Widgets/Images/ImageryProviders/${properties.icon}.png`;
      return new Cesium.ProviderViewModel({
        category: properties.category,
        creationFunction: () =>
          new Cesium[properties.type](
            properties.type == "TileMapServiceImageryProvider"
              ? { url: Cesium.buildModuleUrl(properties.args.url) }
              : properties.type == "createWorldImagery"
              ? { style: Cesium.IonWorldImageryStyle[properties.arg] }
              : properties.args
          ),
        name: name,
        iconUrl: Cesium.buildModuleUrl(iconUrl),
        tooltip: properties.tooltip,
      });
    }
  );
  viewer = new Cesium.Viewer("map", {
    timeline: false,
    geocoder: false,
    animation: false,
    selectionIndicator: false,
    imageryProviderViewModels: providerViewModels,
  });
  viewer.scene.primitives.add(polylines);
  viewer.scene.postProcessStages.fxaa.enabled = true;
  $(".cesium-baseLayerPicker-dropDown > div").slice(2, 4).hide();
  labels = viewer.scene.primitives.add(new Cesium.LabelCollection());
  handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
  handler.setInputAction(onClick3d, Cesium.ScreenSpaceEventType.LEFT_CLICK);
  handler.setInputAction(onRightClick3d, Cesium.ScreenSpaceEventType.RIGHT_CLICK);
  handler.setInputAction(changeCursor, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
}

function switchLayer(layerType) {
  map.removeLayer(layer);
  layer = L.tileLayer(layers[layerType]);
  map.addLayer(layer);
}

function changeMarker(type) {
  markerType = type;
  displayNetwork();
}

function createNode(node, nodeType) {
  if (!node.latitude && !node.longitude) return;
  geographicalDevices[node.id] = node;
  (dimension == "2D" ? createNode2d : createNode3d)(node, nodeType);
}

function createNode3d(node, nodeType) {
  const icon = nodeType === "device" ? node.icon || "router" : "site";
  markersArray.push(
    viewer.entities.add({
      properties: node,
      position: Cesium.Cartesian3.fromDegrees(node.longitude, node.latitude),
      billboard: {
        image: `../static/img/view/3D/${icon}.gif`,
        scaleByDistance: new Cesium.NearFarScalar(1.5e2, 2.0, 1.5e7, 0.5),
      },
      label: {
        fillColor: Cesium.Color.BLACK,
        text: node.name,
        scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.5, 8.0e6, 0.0),
        pixelOffset: new Cesium.Cartesian2(0.0, 20.0),
        font: "20px sans-serif",
      },
    })
  );
}

function createNode2d(node, nodeType) {
  let marker;
  try {
    marker =
      markerType == "Circle Marker"
        ? L.circleMarker([node.latitude, node.longitude])
        : markerType == "Circle"
        ? L.circle([node.latitude, node.longitude])
        : L.marker([node.latitude, node.longitude]);
  } catch (err) {
    return console.error(`Device '${node.name}' couldn't be loaded (${err})`);
  }
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
  marker.on("click", function (e) {
    if (nodeType == "site") {
      showPoolView(node.id);
    } else {
      showTypePanel(nodeType, node.id);
    }
  });
  marker.on("contextmenu", function (e) {
    $(".menu").hide();
    $(`.rc-${nodeType}-menu`).show();
    selectedObject = node;
  });
  if (clustered) {
    markerGroup.addLayer(marker);
  } else {
    marker.addTo(map);
  }
}

function createLink(link) {
  geographicalLinks[link.id] = link;
  (dimension == "2D" ? createLink2d : createLink3d)(link);
}

function createLink3d(link) {
  const color = Cesium.Color.fromCssColorString(link.color.trim()) || "#000000";
  polylinesArray.push(
    polylines.add({
      id: link.id,
      positions: Cesium.Cartesian3.fromDegreesArray([
        link.source_longitude,
        link.source_latitude,
        link.destination_longitude,
        link.destination_latitude,
      ]),
      material: Cesium.Material.fromType("Color", {
        color: color,
      }),
      width: 1,
    })
  );

  labels.add({
    // eslint-disable-next-line new-cap
    position: new Cesium.Cartesian3.fromDegrees(...computeLinkMiddle(link), 0.0),
    scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.5, 8.0e6, 0.0),
    fillColor: Cesium.Color.BLACK,
    text: link.name,
  });
}

function computeLinkMiddle(link) {
  const [φ1, φ2, λ1, λ2] = [
    link.source_latitude,
    link.destination_latitude,
    link.source_longitude,
    link.destination_longitude,
  ].map((coordinate) => (coordinate * Math.PI) / 180);
  const Bx = Math.cos(φ2) * Math.cos(λ2 - λ1);
  const By = Math.cos(φ2) * Math.sin(λ2 - λ1);
  const φ3 = Math.atan2(
    Math.sin(φ1) + Math.sin(φ2),
    Math.sqrt((Math.cos(φ1) + Bx) * (Math.cos(φ1) + Bx) + By * By)
  );
  const λ3 = λ1 + Math.atan2(By, Math.cos(φ1) + Bx);
  return [λ3 * (180 / Math.PI), φ3 * (180 / Math.PI)];
}

function createLink2d(link) {
  if (clustered) return;
  let pointA = new L.LatLng(link.source_latitude, link.source_longitude);
  let pointB = new L.LatLng(link.destination_latitude, link.destination_longitude);
  const pointList = [pointA, pointB];
  const polyline = new L.Polyline(pointList, {
    color: link.color,
    weight: 2,
    opacity: 1,
    smoothFactor: 1,
  });
  polylinesArray.push(polyline);
  polyline.link_id = link.id;
  polyline.on("click", function (e) {
    showTypePanel("link", this.link_id);
  });
  polyline.on("contextmenu", function (e) {
    $(".menu").hide();
    $(".rc-link-menu").show();
    selectedObject = link;
  });
  polyline.bindTooltip(link.name, {
    permanent: false,
  });
  polyline.addTo(map);
}

function deleteAllDevices() {
  for (let i = 0; i < markersArray.length; i++) {
    if (dimension == "3D") {
      viewer.entities.remove(markersArray[i]);
    } else if (clustered) {
      markerGroup.removeLayer(markersArray[i]);
    } else {
      markersArray[i].removeFrom(map);
    }
  }
  markersArray = [];
}

function deleteAllLinks() {
  polylinesArray.map((polyline) => {
    if (dimension == "2D") {
      polyline.removeFrom(map);
    } else {
      polylines.remove(polyline);
    }
  });
  polylinesArray = [];
}

function deleteAll() {
  deleteAllDevices();
  deleteAllLinks();
}

Object.assign(action, {
  "Open Street Map": () => switchLayer("osm"),
  "Google Maps": () => switchLayer("gm"),
  Image: () => changeMarker("Image"),
  Circle: () => changeMarker("Circle"),
  "Circle Marker": () => changeMarker("Circle Marker"),
  Normal: () => displayNetwork(),
  Clustered: () => displayNetwork(true),
});

function displayNetwork(withCluster) {
  deleteAll();
  clustered = withCluster;
  if ($("#view-type").prop("checked")) {
    call({
      url: "/get_view_topology",
      callback: function (topology) {
        topology.devices.map((d) => createNode(d, "device"));
        topology.links.map(createLink);
      },
    });
  } else {
    $(".menu").hide();
    call({
      url: "/get_all/pool",
      callback: function (pools) {
        for (let i = 0; i < pools.length; i++) {
          if (pools[i].longitude) {
            createNode(pools[i], "site");
          }
        }
      },
    });
    $(".geo-menu").show();
  }
  if (dimension == "2D") {
    map[clustered ? "addLayer" : "removeLayer"](markerGroup);
  }
}

function deviceToNode(device) {
  const logicalDevice = {
    id: device.id,
    label: device.name,
    image: `/static/img/view/3D/${device.icon}.gif`,
    shape: "image",
  };
  logicalDevices[device.id] = device;
  return logicalDevice;
}

function linkToEdge(link) {
  const logicalLink = {
    id: link.id,
    from: link.source_id,
    to: link.destination_id,
  };
  logicalLinks[link.id] = link;
  return logicalLink;
}

function showPoolView(poolId) {
  jsPanel.create({
    id: `pool-view-${poolId}`,
    container: ".right_column",
    theme: "none",
    border: "medium",
    headerTitle: "Site view",
    position: "center-top 0 58",
    contentSize: "1000 600",
    content: `
      <div id="network-${poolId}" style="height:100%; width:100%;"></div>
    `,
    dragit: {
      opacity: 0.7,
      containment: [5, 5, 5, 5],
    },
  });
  call({
    url: `/get/pool/${poolId}`,
    callback: function (pool) {
      $(`#network-${poolId}`).contextMenu({
        menuSelector: "#contextMenu",
        menuSelected: function (selectedMenu) {
          const row = selectedMenu.text();
          action[row](selected);
        },
      });
      displayPool(poolId, pool.devices, pool.links);
    },
  });
}

function displayPool(poolId, nodes, edges) {
  let container = document.getElementById(`network-${poolId}`);
  nodes = new vis.DataSet(nodes.map(deviceToNode));
  edges = new vis.DataSet(edges.map(linkToEdge));
  const network = new vis.Network(container, { nodes: nodes, edges: edges }, {});
  network.on("oncontext", function (properties) {
    properties.event.preventDefault();
    const node = this.getNodeAt(properties.pointer.DOM);
    const edge = this.getEdgeAt(properties.pointer.DOM);
    if (typeof node !== "undefined") {
      $(".menu").hide();
      $(".rc-device-menu").show();
      selected = logicalDevices[node];
    } else if (typeof edge !== "undefined") {
      selected = logicalLinks[edge];
      $(".menu").hide();
      $(".rc-link-menu").show();
    } else {
      $(".menu").hide();
      $(".insite-menu").show();
    }
  });
}

function changeCursor(click) {
  const instance = viewer.scene.pick(click.endPosition);
  document.body.style.cursor = instance ? "pointer" : "default";
}

function onRightClick3d(click) {
  const instance = viewer.scene.pick(click.position);
  if (instance) {
    const isLink = typeof instance.id == "number";
    const id = isLink ? instance.id : instance.id._properties._id._value;
    selectedObject = (isLink ? geographicalLinks : geographicalDevices)[id];
    const menu = isLink ? "link" : selectedObject.type == "pool" ? "site" : "device";
    $(".menu").hide();
    $(`.rc-${menu}-menu`).show();
  } else {
    selectedObject = null;
    $(".menu").hide();
  }
}

function onClick3d(click) {
  const instance = viewer.scene.pick(click.position);
  if (instance) {
    const isLink = typeof instance.id == "number";
    const id = isLink ? instance.id : instance.id._properties._id._value;
    const type = isLink ? "link" : instance.id._properties._type._value;
    if (type == "pool") {
      showPoolView(id);
    } else {
      showTypePanel(type, id);
    }
  }
}

function initLogicalView() {
  const viewSettings = visualization.logical;
  call({
    url: "/get_view_topology",
    callback: function (topology) {
      const network = document.getElementById("network");
      // eslint-disable-next-line new-cap
      graph = ForceGraph3D(viewSettings.config)(network);
      graph
        .width($(".main_frame").width() + 20)
        .height($(".main_frame").height() - 90)
        .backgroundColor(theme.view.logical.background)
        .onBackgroundRightClick(() => {
          $(".menu").hide();
        })
        .onNodeHover((node) => (network.style.cursor = node ? "pointer" : null))
        .onNodeClick((node) => {
          const ratio = 1 + 100 / Math.hypot(node.x, node.y, node.z);
          const position = { x: node.x * ratio, y: node.y * ratio, z: node.z * ratio };
          graph.cameraPosition(position, node, 1500);
          setTimeout(() => showTypePanel(node.type, node.id), 1550);
        })
        .onNodeRightClick((node) => {
          $(".menu").show();
          selectedObject = node;
        })
        .onLinkHover((link) => (network.style.cursor = link ? "pointer" : null))
        .onLinkClick((link) => showTypePanel("link", link.id))
        .linkWidth(viewSettings.link_width)
        .linkOpacity(viewSettings.link_opacity)
        .graphData({
          nodes: topology.devices,
          links: topology.links.map((link) => ({
            source: link.source_id,
            target: link.destination_id,
            value: 5,
            ...link,
          })),
        });
      if (viewSettings.display_link_label) {
        graph
          .linkThreeObjectExtend(true)
          .linkThreeObject((link) => {
            const sprite = new SpriteText(link.name);
            sprite.color = theme.view.logical.label;
            sprite.textHeight = 3;
            return sprite;
          })
          .linkPositionUpdate((sprite, { start, end }) => {
            Object.assign(
              sprite.position,
              Object.assign(
                ...["x", "y", "z"].map((c) => ({
                  [c]: start[c] + (end[c] - start[c]) / 2,
                }))
              )
            );
          });
      }
      if (viewSettings.display_link_traffic) {
        graph
          .linkDirectionalParticles("value")
          .linkDirectionalParticleSpeed((d) => d.value * viewSettings.traffic_speed);
      }
      if (viewSettings.display_icons) {
        graph.nodeThreeObject(({ icon }) => {
          const image = new THREE.Mesh(
            new THREE.SphereGeometry(7),
            new THREE.MeshBasicMaterial({
              depthWrite: false,
              transparent: true,
              opacity: 0,
            })
          );
          const sprite = new THREE.Sprite(
            new THREE.SpriteMaterial({
              map: new THREE.TextureLoader().load(`../static/img/view/2D/${icon}.gif`),
            })
          );
          sprite.scale.set(10, 10);
          image.add(sprite);
          return image;
        });
      }
    },
  });
}

export function initView() {
  $("body").contextMenu({
    menuSelector: "#contextMenu",
    menuSelected: function (selectedMenu) {
      const row = selectedMenu.text();
      action[row](selectedObject);
      selectedObject = null;
    },
  });
  Object.assign(action, {
    Properties: (o) => showTypePanel(o.type, o.id),
    Connect: (d) => showConnectionPanel(d),
    Configuration: (d) => showDeviceData(d),
  });
  for (let type of ["device", "link"]) {
    createTooltip({
      autoshow: true,
      persistent: true,
      name: `${type}_filtering`,
      target: `#${type}-filtering`,
      container: `#${type}-filtering-form`,
      size: "700 400",
      position: {
        my: "center-top",
        at: "center-bottom",
        offsetY: 10,
      },
      url: `../form/${type}_filtering`,
      title: `${type.charAt(0).toUpperCase() + type.slice(1)} Filtering`,
    });
  }
  if (page == "logical_view") {
    initLogicalView();
  } else {
    initGeographicalFramework();
    displayNetwork();
    $("#view-type").change(() => displayNetwork());
  }
}

function filterView() {
  const data = {
    device: { form: serializeForm(`#device-filtering-form`) },
    link: { form: serializeForm(`#link-filtering-form`) },
  };
  call({
    url: "/view_filtering",
    data: data,
    callback: function (results) {
      const nodesId = results.device.map((node) => node.id);
      if (page == "logical_view") {
        graph.graphData({
          nodes: results.device,
          links: results.link
            .filter(
              (link) =>
                nodesId.includes(link.source_id) &&
                nodesId.includes(link.destination_id)
            )
            .map((link) => ({
              source: link.source_id,
              target: link.destination_id,
              value: 5,
              ...link,
            })),
        });
        graph.refresh();
      } else {
        deleteAll();
        results.device.map((d) => createNode(d, "device"));
        results.link.map(createLink);
      }
      notify("Filter applied.", "success", 5);
    },
  });
}

configureNamespace("visualization", [showPoolView, filterView]);
