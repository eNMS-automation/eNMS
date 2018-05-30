function showModal(modal_name){
  $(`#${modal_name}`).modal('show');
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

function scheduleScript() {
  if ($("#scheduling-form").parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/tasks/view_scheduler",
      dataType: "json",
      data: $("#scheduling-form").serialize(),
      success: function() {
        alertify.notify('Task scheduled', 'success', 5);
      }
    });
    $("#scheduling").modal('hide');
  } else {
    alertify.notify('Some fields are missing', 'error', 5);
  }
}