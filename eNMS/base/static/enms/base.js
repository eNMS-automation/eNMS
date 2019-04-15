/*
global
alertify: false
jsPanel: false
NProgress: false
propertyTypes: false
table: false
*/

const currentUrl = window.location.href.split("#")[0].split("?")[0];

/**
 * Update link to the docs.
 * @param {url} url - URL pointing to the right page of the docs.
 */
// eslint-disable-next-line
function doc(page) {
  let url = {
    "configuration_management": "https://enms.readthedocs.io/en/latest/inventory/objects.html",
    "device_management": "https://enms.readthedocs.io/en/latest/inventory/objects.html",
    "instance_management": "https://enms.readthedocs.io/en/latest/security/access.html",
    "link_management": "https://enms.readthedocs.io/en/latest/inventory/objects.html",
    "user_management": "https://enms.readthedocs.io/en/latest/security/access.html",
  }[page]
  $("#doc-link").attr("href", url);
}

/**
 * Open new tab at the provided URL.
 * @param {url} url - URL.
 */
function openUrl(url) {
  let win = window.open(url, "_blank");
  win.focus();
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
function initTable(type, toExclude) {
  // eslint-disable-next-line new-cap
  const table = $("#table").DataTable({
    serverSide: true,
    orderCellsTop: true,
    scrollX: true,
    sDom: "<'top'i>rt<'bottom'lp><'clear'>",
    ajax: {
      url: `/server_side_processing/${type}`,
      data: (d) => {
        data = JSON.parse(JSON.stringify($("#filter-form").serializeArray()));
        result = {"pools": []}
        data.forEach((property) => {
          if (property.name == "pools") {
            result.pools.push(property.value);
          } else {
            result[property.name] = property.value
          }
        });
        d.form = result;
      },
    },
  });
  return table;
}

/**
 * Server-side table filtering.
 */
// eslint-disable-next-line
function filterTable() {
  table.ajax.reload(null, false);
  alertify.notify("Filter applied.", "success", 5);
}

/**
 * Datatable periodic refresh.
 * @param {interval} interval - Refresh interval.
 */
// eslint-disable-next-line
function refreshTable(interval) {
  table.ajax.reload(null, false);
  setTimeout(() => refreshTable(interval), 5000);
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
 * Configure panel.
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
 * Show Filtering Panel
 */
// eslint-disable-next-line
function showFilteringPanel(type) {
  createPanel(
    "filtering-panel",
    "700 700",
    `../${type}_filtering_form`,
    function(panel) {
      panel.content.innerHTML = this.responseText;
      panel.setHeaderTitle("Device automation");
      configureForm(`${type}_filtering`);
    }
  );
}

/**
 * Connect to a device.
 */
// eslint-disable-next-line
function showAutomationPanel(id) {
  createPanel(
    `automation-panel-${id}`,
    "400 200",
    "../device_automation_form",
    function(panel) {
      panel.content.innerHTML = this.responseText;
      panel.setHeaderTitle("Device automation");
      configureForm("device_automation");
      $("#device-automation-form").prop("id", `${id}-device-automation-form`);
      $("#device-automation-button").prop("id", `${id}-device-automation-button`);
      $(`#${id}-device-automation-button`).attr("onclick", `saveDeviceJobs(${id})`);
    }
  );
}

/**
 * Connect to a device.
 */
// eslint-disable-next-line
function showConnectionPanel(id) {
  createPanel(
    `connection-panel-${id}`,
    "400 600",
    "../connection_form",
    function(panel) {
      panel.content.innerHTML = this.responseText;
      panel.setHeaderTitle("Connect to device");
      $("#connection-parameters-form").prop("id", `${id}-connection-parameters-form`);
      $("#connection-button").prop("id", `${id}-connection-button`);
      $(`#${id}-connection-button`).attr("onclick", `sshConnection(${id})`);
    }
  );
}

/**
 * Connect to a device.
 */
// eslint-disable-next-line
function showPoolObjectsPanel(id) {
  createPanel(
    `pool-object-panel-${id}`,
    "400 400",
    "../pool_objects_form",
    function(panel) {
      panel.content.innerHTML = this.responseText;
      panel.setHeaderTitle("Connect to device");
      configureForm("pool_objects");
      $("#pool-objects-form").prop("id", `${id}-pool-objects-form`);
      $("#pool-objects-button").prop("id", `${id}-pool-objects-button`);
      $(`#${id}-pool-objects-button`).attr("onclick", `savePoolObjects(${id})`);
      call(`/get/pool/${id}`, function(pool) {
        $("#devices").selectpicker("val", pool.devices.map((n) => n.id));
        $("#links").selectpicker("val", pool.links.map((l) => l.id));
      });
    }
  );
}

/**
 * Configure form.
 */
function configureForm(form, id) {
  if (!formProperties[form]) return;
  formProperties[form].forEach((property) => {
    const propertyType = propertyTypes[property] || "str";
    el = $(id ? `#${id}-${form}-${property}` : `#${form}-${property}`);
    if (!el.length) el = $(`#${property}`);
    if (propertyType == "date") {
      const today = new Date();
      el.datetimepicker({
        format: "DD/MM/YYYY HH:mm:ss",
        widgetPositioning: {
          horizontal: "left",
          vertical: "bottom",
        },
        useCurrent: false,
      });
    } else {
      el.selectpicker({
        liveSearch: true,
        actionsBox: true,
      });
    }
  });
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
          configureForm(type, id);
          if (["service", "workflow"].includes(type)) panelCode(type, id);
          if (type !== "service") processInstance(type, instance);
        });
      } else {
        configureForm(type);
        panel.setHeaderTitle(`Create a New ${type}`);
        $(`#edit-${type}-form`).trigger("reset");
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
      if (typeof table != "undefined") table.ajax.reload(null, false);
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
  configureForm(page);
  doc(page);
});
