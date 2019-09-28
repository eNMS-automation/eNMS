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

$(function() {
  call(`/count_models`, function(result) {
    for (const type of Object.keys(defaultProperties)) {
      $(`#count-${type}`).text(result.counters[type]);
    }
    for (const [objects, type] of Object.entries(result.properties)) {
      drawDiagrams(type, objects);
    }
  });

  $.each(defaultProperties, function(type, property) {
    $(`#${type}-properties`).on("change", function() {
      call(`/counters/${this.value}/${type}`, function(objects) {
        drawDiagrams(objects, type);
      });
    });
  });
});
