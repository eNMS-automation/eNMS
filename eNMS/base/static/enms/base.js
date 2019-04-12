/*
global
alertify: false
NProgress: false
propertyTypes: false
table: false
*/

const currentUrl = window.location.href.split("#")[0].split("?")[0];
let selects = [];

/**
 * Update link to the docs.
 * @param {url} url - URL pointing to the right page of the docs.
 */
// eslint-disable-next-line
function doc(url) {
  $("#doc-link").attr("href", url);
}

/**
 * Show modal.
 * @param {name} name - Modal name.
 */
// eslint-disable-next-line
function showModal(name) {
  $(`#${name}`).modal("show");
}

/**
 * Reset form and show modal.
 * @param {name} name - Modal name.
 */
// eslint-disable-next-line
function resetShowModal(name) {
  $(`#${name}-form`).trigger("reset");
  $(`#${name}`).modal("show");
}

/**
 * Convert to Bootstrap Select.
 * @param {ids} ids - Ids.
 */
// eslint-disable-next-line
function convertSelect(...ids) {
  ids.forEach((id) => {
    selects.push(id);
    $(id).selectpicker({
      liveSearch: true,
      actionsBox: true,
    });
  });
}

/**
 * Returns partial function.
 * @param {function} func - any function
 * @return {function}
 */
function partial(func, ...args) {
  return function() {
    return func.apply(this, args);
  };
}

/**
 * Capitalize.
 * @param {string} string - Word.
 * @return {capitalizedString}
 */
function capitalize(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * Process results.
 * @param {callback} callback - Callback function.
 * @param {results} results - Results.
 */
function processResults(callback, results) {
  if (!results) {
    alertify.notify("HTTP Error 403 – Forbidden", "error", 5);
  } else if (results.error) {
    alertify.notify(results.error, "error", 5);
  } else {
    callback(results);
  }
}

/**
 * jQuery Ajax Call.
 * @param {url} url - Url.
 * @param {callback} callback - Function to process results.
 */
function call(url, callback) {
  $.ajax({
    type: "POST",
    url: url,
    success: function(results) {
      processResults(callback, results);
    },
  });
}

/**
 * jQuery Ajax Form Call.
 * @param {url} url - Url.
 * @param {form} form - Form.
 * @param {callback} callback - Function to process results.
 */
function fCall(url, form, callback) {
  if (
    $(form)
      .parsley()
      .validate()
  ) {
    $.ajax({
      type: "POST",
      url: url,
      data: $(form).serialize(),
      success: function(results) {
        processResults(callback, results);
      },
    });
  }
}

/**
 * Datatable per-column search.
 * @param {cls} cls - Object class.
 * @param {type} type - Table type.
 * @param {toExclude} toExclude - List of parameters to exclude for search.
 * @return {table}
 */
// eslint-disable-next-line
function initTable(cls, type, toExclude, scrollX) {
  $("#table thead tr")
    .clone(true)
    .appendTo("#table thead");
  $("#table thead tr:eq(1) th").each(function(i) {
    const title = $(this).text();
    if (!toExclude.includes(title)) {
      $(this).html(
        `<input type="text" class="form-control" style="width: 100%;"/>`
      );
      $("input", this).on("keyup change", function() {
        if (table.column(i).search() !== this.value) {
          table
            .column(i)
            .search(this.value)
            .draw();
        }
      });
    } else {
      $(this).empty();
    }
  });
  // eslint-disable-next-line new-cap
  const table = $("#table").DataTable({
    serverSide: true,
    orderCellsTop: true,
    scrollX: scrollX || false,
    sDom: "<'top'i>rt<'bottom'lp><'clear'>",
    ajax: {
      url: `/server_side_processing/${cls}/${type}`,
      data: (d) => {
        d.pools = $("#restrict-pool").val();
      },
    },
  });
  return table;
}

/**
 * Datatable periodic refresh.
 * @param {interval} interval - Refresh interval.
 */
// eslint-disable-next-line
function refreshTable(interval) {
  table.ajax.reload(null, false);
  setTimeout(partial(refreshTable, interval), 5000);
}

/**
 * Delete object.
 * @param {type} type - Node or link.
 * @param {id} id - Id of the object to delete.
 */
// eslint-disable-next-line
function confirmDeletion(type, id) {
  $("#confirm-delete-button").attr(
    "onclick",
    `deleteInstance('${type}', ${id})`
  );
  $("#confirm-delete").modal("show");
}

/**
 * Delete object.
 * @param {type} type - Node or link.
 * @param {id} id - Id of the object to delete.
 */
// eslint-disable-next-line
function deleteInstance(type, id) {
  call(`/delete/${type}/${id}`, function(result) {
    $("#confirm-delete").modal("hide");
    table
      .row($(`#${id}`))
      .remove()
      .draw(false);
    alertify.notify(
      `${capitalize(type)} '${result.name}' deleted.`,
      "error",
      5
    );
  });
}

/**
 * Display type modal for creation.
 * @param {type} type - Type.
 */
// eslint-disable-next-line
function showCreateModal(type) {
  $(`#edit-${type}-form`).trigger("reset");
  $(`#${type}-id`).val("");
  selects.forEach((id) => $(id).selectpicker("render"));
  $(`#title-${type}`).text(`Create a New ${type}`);
  $(`#edit-${type}`).modal("show");
}

/**
 * Display instance modal for editing.
 * @param {type} type - Type.
 * @param {instance} instance - Object instance.
 * @param {dup} dup - Edit versus duplicate.
 */
function processInstance(type, instance, dup) {
  const mode = dup ? "Duplicate" : "Edit";
  $(`#title-${type}`).text(`${mode} ${type} '${instance.name}'`);
  for (const [property, value] of Object.entries(instance)) {
    const propertyType = propertyTypes[property] || "str";
    if (propertyType.includes("bool") || property.includes("regex")) {
      $(`#${type}-${property}`).prop("checked", value);
    } else if (propertyType.includes("dict")) {
      $(`#${type}-${property}`).val(value ? JSON.stringify(value) : "{}");
    } else if (propertyType.includes("list") || propertyType.includes("obj")) {
      $(`#${type}-${property}`).selectpicker("deselectAll");
      $(`#${type}-${property}`).selectpicker(
        "val",
        propertyType === "object"
          ? value.id
          : propertyType === "list"
          ? value
          : value.map((p) => p.id)
      );
      $(`#${type}-${property}`).selectpicker("render");
    } else if (propertyType == "object") {
      $(`#${type}-${property}`).selectpicker("deselectAll");
      $(`#${type}-${property}`).selectpicker("val", value.id);
      $(`#${type}-${property}`).selectpicker("render");
    } else {
      $(`#${type}-${property}`).val(value);
    }
  }
  if (dup) instance.id = instance.name = "";
  $(`#edit-${type}`).modal("show");
}

/**
 * Display instance modal for editing.
 * @param {type} type - Type.
 * @param {id} id - Instance ID.
 * @param {dup} dup - Edit versus duplicate.
 */
// eslint-disable-next-line
function showTypeModal(type, id, dup) {
  call(`/get/${type}/${id}`, function(instance) {
    processInstance(type, instance, dup);
  });
}

/**
 * Save instance.
 * @param {type} type - Type.
 * @param {instance} instance - Object instance.
 * @param {hideModal} hideModal - Hide edit modal after saving.
 */
function saveInstance(type, instance, hideModal = true) {
  const title = $(`#title-${type}`)
    .text()
    .startsWith("Edit");
  const mode = title ? "edit" : "create";
  const message = `${capitalize(type)} '${instance.name}'
  ${mode == "edit" ? "edited" : "created"}.`;
  alertify.notify(message, "success", 5);
  if (hideModal) {
    $(`#edit-${type}`).modal("hide");
  }
}

/**
 * Create or edit instance.
 * @param {type} type - Type.
 */
// eslint-disable-next-line
function processData(type) {
  fCall(`/update/${type}`, `#edit-${type}-form`, function(instance) {
    saveInstance(type, instance);
    if (table) {
      table.ajax.reload(null, false);
    }
  });
}

/**
 * Sidebar initialization.
 */
function initSidebar() {
  let setContentHeight = function() {
    $(".right_col").css("min-height", $(window).height());
    let bodyHeight = $("body").outerHeight();
    let footerHeight = $("body").hasClass("footer_fixed")
      ? -10
      : $("footer").height();
    let leftColHeight =
      $(".left_col")
        .eq(1)
        .height() + $(".sidebar-footer").height();
    let contentHeight = bodyHeight < leftColHeight ? leftColHeight : bodyHeight;
    contentHeight -= $(".nav_menu").height() + footerHeight;
    $(".right_col").css("min-height", contentHeight);
  };

  $("#sidebar-menu")
    .find("a")
    .on("click", function(ev) {
      let $li = $(this).parent();
      if ($li.is(".active")) {
        $li.removeClass("active active-sm");
        $("ul:first", $li).slideUp(function() {
          setContentHeight();
        });
      } else {
        // prevent closing menu if we are on child menu
        if (!$li.parent().is(".child_menu")) {
          $("#sidebar-menu")
            .find("li")
            .removeClass("active active-sm");
          $("#sidebar-menu")
            .find("li ul")
            .slideUp();
        } else {
          if ($("body").is(".nav-sm")) {
            $("#sidebar-menu")
              .find("li")
              .removeClass("active active-sm");
            $("#sidebar-menu")
              .find("li ul")
              .slideUp();
          }
        }
        $li.addClass("active");
        $("ul:first", $li).slideDown(function() {
          setContentHeight();
        });
      }
    });

  $("#menu_toggle").on("click", function() {
    if ($("body").hasClass("nav-md")) {
      $("#sidebar-menu")
        .find("li.active ul")
        .hide();
      $("#sidebar-menu")
        .find("li.active")
        .addClass("active-sm");
      $("#sidebar-menu")
        .find("li.active")
        .removeClass("active");
    } else {
      $("#sidebar-menu")
        .find("li.active-sm ul")
        .show();
      $("#sidebar-menu")
        .find("li.active-sm")
        .addClass("active");
      $("#sidebar-menu")
        .find("li.active-sm")
        .removeClass("active-sm");
    }
    $("body").toggleClass("nav-md nav-sm");
    setContentHeight();
    $(".dataTable").each(function() {
      $(this)
        .dataTable()
        .fnDraw();
    });
  });

  // check active menu
  const url = "a[href='" + currentUrl + "']";
  $("#sidebar-menu")
    .find(url)
    .parent("li")
    .addClass("current-page");
  $("#sidebar-menu")
    .find("a")
    .filter(function() {
      return this.href == currentUrl;
    })
    .parent("li")
    .addClass("current-page")
    .parents("ul")
    .slideDown(function() {
      setContentHeight();
    })
    .parent()
    .addClass("active");

  setContentHeight();
  if ($.fn.mCustomScrollbar) {
    $(".menu_fixed").mCustomScrollbar({
      autoHideScrollbar: true,
      theme: "minimal",
      mouseWheel: { preventDefault: true },
    });
  }
}

if (typeof NProgress != "undefined") {
  $(document).ready(function() {
    NProgress.start();
  });
  $(window).load(function() {
    NProgress.done();
  });
}

$(document).ready(function() {
  initSidebar();
});
