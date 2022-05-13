$('.tr-doctable').hover(function() {
  const rowname = $(this).attr('rowname');
  temp = $(`[rowname='${rowname}']`);
  for (x= 0; x < temp.length; x++) {
    $(temp[x]).css('background-color', '#EAEAEA');
  }
}, function(){
  const rowname = $(this).attr('rowname');
  temp = $(`[rowname='${rowname}']`);
  for (x= 0; x < temp.length; x++) {
    $(temp[x]).css('background-color', 'white');
  }
});
