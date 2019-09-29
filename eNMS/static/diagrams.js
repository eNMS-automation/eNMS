/*
global
echarts: false
*/

function drawDiagrams(diagram, data) {
  diagram.setOption({
    tooltip: {
      formatter: "{b} : {c} ({d}%)",
    },
    series: [
      {
        type: "pie",
        data: data,
      },
    ],
  });
}

function computeData(objects) {
  let data = [];
  for (const [key, value] of Object.entries(objects)) {
    data.push({
      value: value,
      name: key,
      itemStyle: {
        normal: {
          color: "#c23531",
        },
      },
    });
  }
  console.log(data);
  return data;
}
