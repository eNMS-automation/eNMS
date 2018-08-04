function showScriptModal(type, id) {
  $.ajax({
    type: "POST",
    url: `/scripts/get/${type}/${id}`,
    success: function(properties){
      $('#title').text(`Edit ${properties.name} properties`);
      for (const [property, value] of Object.entries(properties)) {
        if(typeof(value) === "boolean") {
          $(`#${type}-${property}`).prop('checked', value);
        } else {
          var gValue = property == 'payload' ? JSON.stringify(value) : value;
          $(`#${type}-${property}`).val(gValue);
        }
      }
    }
  });
  $(`#edit-${type}`).modal('show');
}