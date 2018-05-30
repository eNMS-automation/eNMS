var nodeTable = $('#node-table').DataTable()
    linkTable = $('#link-table').DataTable()

document.getElementById("file").onchange = function() {
  $("#form").submit();
};

function showModal(type) {
  $('#title').text(`Add a new ${type}`);
  $(`#edit-${type}-form`).trigger("reset");
  $(`#edit-${type}`).modal('show');
}

function showObjectModal(type, id) {
  $('#title').text(`Edit ${type} properties`);
  $.ajax({
    type: "POST",
    url: `/objects/get/${type}/${id}`,
    success: function(properties){
      for (const [property, value] of Object.entries(properties)) {
        $(`#${type}-${property}`).val(value);
      }
    }
  });
  $(`#edit-${type}`).modal('show');
}

function editObject(type) {
  if ($(`#edit-${type}-form`).parsley().validate()) {
    $.ajax({
      type: "POST",
      url: "/objects/edit_object",
      dataType: "json",
      data: $(`#edit-${type}-form`).serialize(),
      success: function(properties) {
        var fields = type == 'node' ? node_fields : link_fields
            table = type == 'node' ? nodeTable : linkTable
            mode = $('#title').text() == `Edit ${type} properties` ? 'edit' : 'add'
            result = {}
            values = [];
        console.log(table)
        $.each($(`#edit-${type}-form`).serializeArray(), function() {
          result[this.name] = this.value;
        });
        var name = result.name;
        for (i = 0; i < fields.length; i++) {
          var truncate = ["longitude", "latitude"].includes(fields[i]);
          value = truncate ? parseFloat(result[fields[i]]).toFixed(2) : result[fields[i]]
          values.push(`${value}`);
        }
        values.push(
          `<button type="button" class="btn btn-info btn-xs" onclick="showObjectModal('${type}', '${properties.id}')">Edit</button>`,
          `<button type="button" class="btn btn-danger btn-xs" onclick="deleteObject('${type}', '${properties.id}')">Delete</button>`,
        );
        if (mode == 'edit') {
          table.row($(`#${type}-${properties.id}`)).data(values);
        } else {
          var rowNode = table.row.add(values).draw(false).node();
          $(rowNode).attr("id", `${type}-${properties.id}`);
        }
        message = `Object ${properties.name} ` + (mode == 'edit' ? 'edited !' : 'created !')
        alertify.notify(message, 'success', 5);
      }
    });
    $(`#edit-${type}`).modal('hide');
  }
}

function deleteObject(type, id) {
  $.ajax({
    type: "POST",
    url: `/objects/delete/${type}/${id}`,
    success: function(properties){
      var table = type == 'node' ? nodeTable : linkTable
      table.row($(`#${type}-${id}`)).remove().draw(false);
      alertify.notify(`Object ${properties.name} deleted`, 'error', 5);
    }
  });
}