var schedule = scheduleTask;

function showModal(modal_name){
  $(`#${modal_name}`).modal('show');
  console.log('test');
  }

function connectToDevice(name) {
  var name = $(`#node-name`).val();
  $.ajax({
    type: "POST",
    url: `/views/connect_to_${name}`,
    success: function(msg){
      alertify.notify(`Connection to ${name}`, 'success', 5);
    }
  });
}