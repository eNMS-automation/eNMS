/*
global
alertify: false
jsPanel: false
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
  panel = jsPanel.create({
    id: "deletion-panel",
    theme: "none",
    border: "medium",
    headerTitle: "Delete",
    position: "center-top 0 58",
    contentSize: "300 150",
    content: `
      <div class="modal-body">
        Are you sure you want to permanently remove this item ?
      </div>
      <div class="modal-footer">
        <center>
          <button
            type="button"
            class="btn btn-danger"
            onclick="deleteInstance('${type}', ${id})"
          >Delete</button>
        </center>
      </div>`,
    dragit: {
      opacity: 0.7,
      containment: [5, 5, 5, 5],
    },
  });
}

/**
 * Delete object.
 * @param {type} type - Node or link.
 * @param {id} id - Id of the object to delete.
 */
// eslint-disable-next-line
function deleteInstance(type, id) {
  call(`/delete/${type}/${id}`, function(result) {
    $("#deletion-panel").remove();
    table
      .row($(`#${id}`))
      .remove()
      .draw(false);
    alertify.notify(
      `${type.toUpperCase()} '${result.name}' deleted.`,
      "error",
      5
    );
  });
}

/**
 * Create a panel.
 * @param {id} id - Instance ID.
 * @param {contentSize} contentSize - Content size.
 * @param {url} url - URL to fetch the content from.
 * @param {processing} processing - Function once panel is loaded.
 */
// eslint-disable-next-line
function createPanel(id, contentSize, url, processing) {
  return jsPanel.create({
    id: id,
    theme: "none",
    headerLogo: "../static/images/logo.png",
    headerControls: {
      size: "xl",
    },
    contentOverflow: 'hidden scroll',
    contentSize: contentSize,
    position: "center-top 0 58",
    contentAjax: {
      url: url,
      done: processing,
    },
    dragit: {
      opacity: 0.6,
    },
  });
}

/**
 * Connect to a device.
 */
// eslint-disable-next-line
function showConnectionPanel() {
  createPanel("connection-panel", "200 500", "../${connection}_form");
}

/**
 * Display instance modal for editing.
 * @param {type} type - Type.
 * @param {id} id - Instance ID.
 * @param {duplicate} duplicate - Edit versus duplicate.
 */
// eslint-disable-next-line
function showTypePanel(type, id, duplicate) {
  if ($(`#${id}-edit-${type}-form`).length) {
    return;
  }
  createPanel(
    id ? `panel-${type}-${id}` : `panel-${type}`,
    "700 500",
    `../${type}_form`,
    function(panel) {
      panel.content.innerHTML = this.responseText;
      if (id) {
        call(`/get/${type}/${id}`, function(instance) {
          panel.setHeaderTitle(`${duplicate ? "Duplicate" : "Edit"} ${type} - ${instance.name}`);
          $(`#edit-${type}-form`).prop("id", `${id}-edit-${type}-form`);
          $("#save").prop("id", `${id}-save`);
          $(`#${id}-save`).attr("onclick", `processData("${type}", ${id})`);
          for (let el of $(`[id^=${type}]`)) {
            if (duplicate && ["name", "id"].includes(el.name)) continue;
            $(el).prop("id", `${id}-${el.id}`);
          }
          if (["service", "workflow"].includes(type)) panelCode(type, id);
          if (type !== "service") processInstance(type, instance);
        });
      } else {
        panel.setHeaderTitle(`Create a New ${type}`);
        $(`#edit-${type}-form`).trigger("reset");
        selects.forEach((id) => $(id).selectpicker("render"));
        if (["service", "workflow"].includes(type)) panelCode(type);
      }
    }
  );
}

/**
 * Display instance modal for editing.
 * @param {type} type - Type.
 * @param {instance} instance - Object instance.
 */
function processInstance(type, instance) {
  for (const [property, value] of Object.entries(instance)) {
    el = $(instance ? `#${instance.id}-${type}-${property}` : `#${type}-${property}`);
    const propertyType = propertyTypes[property] || "str";
    if (propertyType.includes("bool") || property.includes("regex")) {
      el.prop("checked", value);
    } else if (propertyType.includes("dict")) {
      el.val(value ? JSON.stringify(value) : "{}");
    } else if (propertyType == "date") {
      const today = new Date();
      el.datetimepicker({
        format: "DD/MM/YYYY HH:mm:ss",
        widgetPositioning: {
          horizontal: "left",
          vertical: "bottom",
        },
        useCurrent: false,
      });
      if (el.length) el.data("DateTimePicker").minDate(today);
      el.val(value);
    } else if (propertyType.includes("list") || propertyType.includes("obj")) {
      el.selectpicker("deselectAll");
      el.selectpicker(
        "val",
        propertyType === "object"
          ? value.id
          : propertyType === "list"
          ? value
          : value.map((p) => p.id)
      );
      el.selectpicker("render");
    } else if (propertyType == "object") {
      el.selectpicker("deselectAll");
      el.selectpicker("val", value.id);
      el.selectpicker("render");
    } else {
      el.val(value);
    }
  }
}

/**
 * Create or edit instance.
 * @param {type} type - Type.
 */
// eslint-disable-next-line
function processData(type, id) {
  fCall(
    `/update/${type}`,
    id ? `#${id}-edit-${type}-form` : `#edit-${type}-form`,
    (instance) => {
      table && table.ajax.reload(null, false);
      $(id ? `#panel-${type}-${id}` : `#panel-${type}`).remove();
      if (type == "service") saveService(instance);
      alertify.notify(
        `${type.toUpperCase()} '${instance.name}' ${
          id ? "updated" : "created"
        }`,
        "success",
        5
      );
    }
  );
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
