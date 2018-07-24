function createScript(type) {
  if ($(`#${type}-form`).parsley().validate() ) {
    var formData = new FormData($(`#${type}-form`)[0]);
    $.ajax({
    type: "POST",
    url: `/scripts/create_script_${type}`,
    dataType: "json",
    data: formData,
    contentType: false,
    cache: false,
    processData: false,
    async: false,
    success: function() {
      alertify.notify("Script created", 'success', 5);
    }
    });
  }
}