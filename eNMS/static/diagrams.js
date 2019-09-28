/*
global
echarts: false
*/

const theme = {
  color: [
    "#26B99A",
    "#34495E",
    "#BDC3C7",
    "#3498DB",
    "#9B59B6",
    "#8abb6f",
    "#759c6a",
    "#bfd3b7",
  ],
};

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
    });
  }
  return data;
}
