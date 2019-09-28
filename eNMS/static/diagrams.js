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
      trigger: "item",
      formatter: "{a} <br/>{b} : {c} ({d}%)",
    },
    calculable: true,
    legend: {
      x: "center",
      y: "bottom",
      data: data,
    },
    toolbox: {
      show: true,
      feature: {
        magicType: {
          show: true,
          type: ["pie", "funnel"],
          option: {
            funnel: {
              x: "25%",
              width: "50%",
              funnelAlign: "center",
              max: 1548,
            },
          },
        },
      },
    },
    series: [
      {
        name: name,
        type: "pie",
        radius: ["35%", "55%"],
        itemStyle: {
          normal: {
            label: {
              show: true,
            },
            labelLine: {
              show: true,
            },
          },
          emphasis: {
            label: {
              show: true,
              position: "center",
              textStyle: {
                fontSize: "14",
                fontWeight: "normal",
              },
            },
          },
        },
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
