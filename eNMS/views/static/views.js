function connectToDevice(name) {
  var name = $(`#node-name`).val();
  $.ajax({
    type: "POST",
    url: `/views/connect_to_${name}`,
    success: function(msg) {
      alertify.notify(`Connection to ${name}.`, 'success', 5);
    }
  });
}