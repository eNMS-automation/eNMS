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

function drawDiagrams(diagram, name, data) {
  diagram.setOption({
    tooltip: {
      formatter: "{a} <br/>{b} : {c} ({d}%)",
    },
    series: [
      {
        name: name,
        type: "pie",
        radius: ["35%", "55%"],
        data: data,
      },
    ],
  });
  return diagram;
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
