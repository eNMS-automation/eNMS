import { call, configureNamespace, notify, openPanel } from "./base.js";

const container = document.getElementById("network");

let currentLabel;
let mousePosition;
export let edges;
export let nodes;
export let triggerMenu;

export function configureGraph(instance, graph, options) {
  nodes = new vis.DataSet(graph.nodes);
  edges = new vis.DataSet(graph.edges);
  for (const [id, label] of Object.entries(instance.labels)) {
    drawLabel(id, label);
  }
  graph = new vis.Network(container, { nodes: nodes, edges: edges }, options);
  graph.setOptions({ physics: false });
  for (const objectType of ["Node", "Edge"]) {
    graph.on(`hover${objectType}`, function () {
      graph.canvas.body.container.style.cursor = "pointer";
    });
    graph.on(`blur${objectType}`, function () {
      graph.canvas.body.container.style.cursor = "default";
    });
  }
  graph.on("oncontext", function (properties) {
    if (triggerMenu) mousePosition = properties.pointer.canvas;
  });
  graph.on("doubleClick", function (event) {
    mousePosition = event.pointer.canvas;
  });
  return graph;
}

export function showLabelPanel({ label, usePosition }) {
  if (!usePosition) mousePosition = null;
  openPanel({
    name: "workflow_label",
    title: label ? "Edit label" : "Create a new label",
    callback: () => {
      if (label) {
        $("#workflow_label-text").val(label.label);
        $("#workflow_label-alignment").val(label.font.align).selectpicker("refresh");
        currentLabel = label;
      } else {
        currentLabel = null;
      }
    },
  });
}

function createLabel() {
  const pos = mousePosition ? [mousePosition.x, mousePosition.y] : [0, 0];
  call({
    url: `/create_label/${workflow.id}/${pos[0]}/${pos[1]}/${currentLabel?.id}`,
    form: "workflow_label-form",
    callback: function (result) {
      drawLabel(result.id, result);
      $("#workflow_label").remove();
      notify("Label created.", "success", 5);
    },
  });
}

export function drawLabel(id, label) {
  nodes.update({
    id: id,
    shape: "box",
    type: "label",
    font: { align: label.alignment || "center" },
    label: label.content,
    borderWidth: 0,
    color: "#FFFFFF",
    x: label.positions[0],
    y: label.positions[1],
  });
}

export function updateBuilderBindings(action) {
  Object.assign(action, {
    "Create Label": () => showLabelPanel({ usePosition: true }),
    "Create Label Button": () => showLabelPanel({ usePosition: false }),
    "Edit Label": (label) => showLabelPanel({ label: label, usePosition: true }),
  });
  $("#network").contextMenu({
    menuSelector: "#contextMenu",
    menuSelected: function (selectedMenu) {
      const row = selectedMenu.text();
      action[row](selectedObject);
    },
  });
}

export const rectangleSelection = (container, graph, nodes) => {
  const offsetLeft = container.position().left - container.offset().left;
  const offsetTop = container.position().top - container.offset().top;
  let drag = false;
  let DOMRect = {};

  const canvasify = (DOMx, DOMy) => {
    // eslint-disable-next-line new-cap
    const { x, y } = graph.DOMtoCanvas({ x: DOMx, y: DOMy });
    return [x, y];
  };

  const correctRange = (start, end) => (start < end ? [start, end] : [end, start]);

  const selectFromDOMRect = () => {
    const [sX, sY] = canvasify(DOMRect.startX, DOMRect.startY);
    const [eX, eY] = canvasify(DOMRect.endX, DOMRect.endY);
    const [startX, endX] = correctRange(sX, eX);
    const [startY, endY] = correctRange(sY, eY);
    triggerMenu = startX == endX && startY == endY;
    if (triggerMenu) return;
    graph.selectNodes(
      nodes.get().reduce((selected, { id }) => {
        const { x, y } = graph.getPositions(id)[id];
        return startX <= x && x <= endX && startY <= y && y <= endY
          ? selected.concat(id)
          : selected;
      }, [])
    );
  };

  container.on("mousedown", function ({ which, pageX, pageY }) {
    const startX = pageX - this.offsetLeft + offsetLeft;
    const startY = pageY - this.offsetTop + offsetTop;
    if (which === 3) {
      Object.assign(DOMRect, {
        startX: startX,
        startY: startY,
        endX: pageX - this.offsetLeft + offsetLeft,
        endY: pageY - this.offsetTop + offsetTop,
      });
      drag = true;
    }
  });

  container.on("mousemove", function ({ which, pageX, pageY }) {
    if (which === 0 && drag) {
      drag = false;
      graph.redraw();
    } else if (drag) {
      Object.assign(DOMRect, {
        endX: pageX - this.offsetLeft + offsetLeft,
        endY: pageY - this.offsetTop + offsetTop,
      });
      graph.redraw();
    }
  });

  container.on("mouseup", function ({ which }) {
    if (which === 3) {
      drag = false;
      graph.redraw();
      selectFromDOMRect();
    }
  });

  graph.on("afterDrawing", (context) => {
    if (drag) {
      const [startX, startY] = canvasify(DOMRect.startX, DOMRect.startY);
      const [endX, endY] = canvasify(DOMRect.endX, DOMRect.endY);
      context.setLineDash([5]);
      context.strokeStyle = "rgba(78, 146, 237, 0.75)";
      context.strokeRect(startX, startY, endX - startX, endY - startY);
      context.setLineDash([]);
      context.fillStyle = "rgba(151, 194, 252, 0.45)";
      context.fillRect(startX, startY, endX - startX, endY - startY);
    }
  });
};

configureNamespace("builder", [createLabel]);
