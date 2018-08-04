var poolId = null;
var table = $('#table').DataTable();

function addPool(mode, properties) {
  values = [];
  for (var i = 0; i < fields.length; i++) {
    values.push(`${properties[fields[i]]}`);
  }
  values.push(
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showPoolModal('${properties.id}')">Edit properties</button>`,
    `<button type="button" class="btn btn-info btn-xs"
    onclick="showPoolObjects('${properties.id}')">Edit objects</button>`,
    `<button type="button" class="btn btn-danger btn-xs"
    onclick="deletePool('${properties.id}')">Delete</button>`
  );
  if (mode == 'edit') {
    table.row($(`#${properties.id}`)).data(values);
  } else {
    var rowNode = table.row.add(values).draw(false).node();
    $(rowNode).attr("id", `${properties.id}`);
  }
}

(function() {
  for (var i = 0; i < pools.length; i++) {
    addPool('create', pools[i]);
  }
})();

function showModal() {
  $("#title").text("Add a new pool");
  $("#edit-form").trigger("reset");
  $("#edit").modal("show");
}

function showPoolModal(id) {
  $.ajax({
    type: "POST",
    url: `/objects/get_pool/${id}`,
    success: function(properties){
      for (const [property, value] of Object.entries(properties)) {
        if (property.includes("regex")) {
          $(`#${property}`).prop('checked', value);
        } else {
          $(`#${property}`).val(value);
        }
        $('#title').text(`Edit pool properties`);
      }
    }
  });
  $("#edit").modal('show');
}

function showPoolObjects(id) {
  $.ajax({
    type: "POST",
    url: `/objects/get_pool_objects/${id}`,
    success: function(properties){
      $('#nodes').val(properties.nodes.map(n => n.id));
      $('#links').val(properties.links.map(l => l.id));
      poolId = id;
    }
  });
  $("#edit-pool-objects").modal('show');
}

function savePoolObjects() {
  $.ajax({
    type: "POST",
    url: `/objects/save_pool_objects/${poolId}`,
    dataType: "json",
    data: $('#pool-objects-form').serialize(),
    success: function(){
      alertify.notify('Changes saved.', 'success', 5);
    }
  });
  $("#edit-pool-objects").modal('hide');
}

function savePool() {
  if ($('#edit-form').parsley().validate()) {
    $.ajax({
      type: "POST",
      url: `/objects/process_pool`,
      dataType: "json",
      data: $('#edit-form').serialize(),
      success: function(pool){
        var mode = $('#title').text().startsWith('Edit') ? 'edit' : 'add';
        addPool(mode, pool)
        message = `Pool '${pool.name}'
        ${mode == 'edit' ? 'edited !' : 'created !'}.`;
        alertify.notify(message, 'success', 5);
      }
    });
    $('#edit').modal('hide');
  }
}

function deletePool(id) {
  $.ajax({
    type: "POST",
    url: `/objects/delete_pool/${id}`,
    success: function(name){
      table.row($(`#${id}`)).remove().draw(false);
      alertify.notify(`Pool '${name}' successfully deleted.`, 'error', 5);
    }
  });
}

function updatePools(id) {
  $.ajax({
    type: "POST",
    url: "/objects/update_pools",
    success: function(properties){
      alertify.notify('Pools successfully updated.', 'success', 5);
    }
  });
}