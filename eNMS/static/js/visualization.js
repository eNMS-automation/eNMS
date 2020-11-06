/*
global
action: false
Cesium: false
defaultPools: false
ForceGraph3D: false
jsPanel: false
L: false
page: false
SpriteText: false
theme: false
THREE: false
visualization: false
*/

import {
  call,
  configureNamespace,
  createTooltip,
  notify,
  serializeForm,
  showTypePanel,
  openPanel,
} from "./base.js";
import { showConnectionPanel, showDeviceData } from "./inventory.js";
import { showRunServicePanel } from "./automation.js";

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
  layer = L.tileLayer(settings2d.layers[settings2d.tile_layer]);
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
  layer = L.tileLayer(visualization.geographical._2D.layers[layerType]);
  map.addLayer(layer);
}

function changeMarker(type) {
  markerType = type;
  displayNetwork({});
}

function createNode(node, nodeType) {
  if (!node.latitude && !node.longitude) return;
  geographicalDevices[node.id] = node;
  (dimension == "2D" ? createNode2d : createNode3d)(node, nodeType);
}

function createNode3d(node, nodeType) {
  const icon = nodeType === "device" ? node.icon || "router" : "site";
  let entity = {
    properties: node,
    position: Cesium.Cartesian3.fromDegrees(node.longitude, node.latitude),
    billboard: {
      image: `../static/img/view/3D/${icon}.gif`,
      scaleByDistance: new Cesium.NearFarScalar(1.5e2, 2.0, 1.5e7, 0.5),
    },
  };
  if (visualization.geographical._3D.labels.node) {
    entity.label = {
      fillColor: Cesium.Color.BLACK,
      text: node.name,
      scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.5, 8.0e6, 0.0),
      pixelOffset: new Cesium.Cartesian2(0.0, 20.0),
      font: "20px sans-serif",
    };
  }
  markersArray.push(viewer.entities.add(entity));
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
  if (visualization.geographical._3D.labels.link) {
    labels.add({
      // eslint-disable-next-line new-cap
      position: new Cesium.Cartesian3.fromDegrees(...computeLinkMiddle(link), 0.0),
      scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.5, 8.0e6, 0.0),
      fillColor: Cesium.Color.BLACK,
      text: link.name,
    });
  }
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
  Normal: () => displayNetwork({}),
  Clustered: () => displayNetwork({ withCluster: true }),
});

function displayNetwork({ noAlert, withCluster }) {
  const maximumSize = visualization.logical.maximum_size;
  let data = {};
  for (let type of ["device", "link"]) {
    let form = serializeForm(`#search-form-${type}`);
    if (!form.pools) form.pools = defaultPools.map((p) => p.id);
    data[type] = { form: form };
  }
  clustered = withCluster;
  deleteAll();
  if (page == "geographical_view" && !$("#view-type").prop("checked")) {
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
  } else {
    call({
      url: "/view_filtering",
      data: data,
      callback: function (results) {
        if (page == "logical_view") {
          if (
            results.device.length > maximumSize.node ||
            results.link.length > maximumSize.link
          ) {
            return notify(
              `Too many objects to display. Use the device and link
              filtering mechanism to reduce the size of the network`,
              "error",
              5
            );
          }
          update3dGraphData(graph, results.device, results.link);
        } else {
          results.device.map((d) => createNode(d, "device"));
          results.link.map(createLink);
          if (dimension == "2D") {
            map[clustered ? "addLayer" : "removeLayer"](markerGroup);
          }
        }
        if (!noAlert) notify("Filter applied.", "success", 5);
      },
    });
  }
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
          action[row](selectedObject);
        },
      });
      const graph = create3dGraphNetwork(`network-${poolId}`);
      update3dGraphData(graph, pool.devices, pool.links);
    },
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

function create3dGraphNetwork(container) {
  const viewSettings = visualization.logical;
  const network = document.getElementById(container);
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
    .linkCurveRotation("rotation");
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
        })
      );
      const sprite = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: new THREE.TextureLoader().load(`../static/img/view/2D/${icon}.gif`),
          alphaTest: 0.5,
        })
      );
      sprite.scale.set(10, 10);
      image.add(sprite);
      return image;
    });
  }
  return graph;
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
    "Run Service": (d) => showRunServicePanel({ instance: d }),
  });
  for (let type of ["device", "link"]) {
    createTooltip({
      autoshow: true,
      persistent: true,
      name: `${type}_filtering`,
      target: `#${type}-filtering`,
      container: `#search-form-${type}`,
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
    create3dGraphNetwork("network");
    notify("Loading network...", "success", 5);
  } else {
    initGeographicalFramework();
    $("#view-type").change(() => displayNetwork({ noAlert: true }));
  }
  displayNetwork({ noAlert: true });
}

function update3dGraphData(graph, devices, links) {
  const nodesId = devices.map((node) => node.id);
  graph
    .graphData({
      nodes: devices,
      links: links
        .filter(
          (link) =>
            nodesId.includes(link.source_id) && nodesId.includes(link.destination_id)
        )
        .map((link) => {
          return {
            source: link.source_id,
            target: link.destination_id,
            value: 5,
            ...link,
          };
        }),
    })
    .refresh();
}

function clearSearch() {
  for (const table of ["device", "link"]) {
    $(`.search-input-${table},.search-list-${table}`).val("");
    $(".search-relation-dd").val("any").selectpicker("refresh");
    $(".search-relation").val([]).trigger("change");
    $(`.search-select-${table}`).val("inclusion").selectpicker("refresh");
  }
  displayNetwork({ noAlert: true });
  notify("Search parameters cleared.", "success", 5);
}

function saveParameters() {
  call({
    url: "/save_visualization_parameters",
    form: "visualization_parameters-form",
    callback: () => {
      notify("Default pools saved.", "success", 5);
      $("#visualization_parameters").remove();
    },
  });
}

function openVisualizationPanel() {
  openPanel({
    title: "Visualization Parameters",
    name: "visualization_parameters",
    size: "400 200",
    callback: () => {
      call({
        url: "/get_visualization_parameters",
        callback: (pools) => {
          pools.forEach((pool) => {
            $("#default_pools").append(new Option(pool.name, pool.id, false, false));
          });
          $("#default_pools")
            .val(pools.map((pool) => pool.id))
            .trigger("change");
        },
      });
    },
  });
}

configureNamespace("visualization", [
  clearSearch,
  displayNetwork,
  openVisualizationPanel,
  saveParameters,
  showPoolView,
]);
