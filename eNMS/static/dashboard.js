/*
global
call: false
*/

const defaultProperties = {
  device: "model",
  link: "model",
  user: "name",
  service: "vendor",
  workflow: "vendor",
  task: "status",
};

function computeData(objects) {
  let legend = [];
  let data = [];
  for (const [key, value] of Object.entries(objects)) {
    legend.push(key);
    data.push({
      value: value,
      name: key,
    });
  }
  return {"data": data, "legend": legend};
}

$(function() {
  const diagrams = {}
  call(`/count_models`, function(result) {
    for (const type of Object.keys(defaultProperties)) {
      $(`#count-${type}`).text(result.counters[type]);
    }
    for (const [type, objects] of Object.entries(result.properties)) {
      const diagram = echarts.init(document.getElementById(type), theme);
      data = computeData(objects);
      drawDiagrams(diagram, type, data, data);
      diagrams[type] = diagram;
    }
  });

  $.each(defaultProperties, function(type, property) {
    $(`#${type}-properties`).on("change", function() {
      call(`/counters/${this.value}/${type}`, function(objects) {
        data = computeData(objects);
        drawDiagrams(diagrams[type], type, data, data);
      });
    });
  });
});
