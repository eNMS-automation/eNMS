/*
global
alertify: false
csrf_token: false
documentationUrl: false
filteringPanel: false
filteringProperties: false
formProperties: false
job: false
jsPanel: false
NProgress: false
page: false
panelCode: false
Promise: false
properties: false
relations: false
saveService: false
saveWorkflow: false
saveWorkflowEdge: false
table: false
type: false
workflowRunMode: false
*/

const currentUrl = window.location.href.split("#")[0].split("?")[0];

const panelSize = {
  add_jobs: "800 500",
  changelog: "700 300",
  changelog_filtering: "700 300",
  cluster: "700 200",
  connection: "400 500",
  configuration: "1200 700",
  configuration_filtering: "700 600",
  database_deletion: "700 400",
  database_migration: "700 300",
  device: "700 500",
  device_filtering: "700 600",
  device_results: "1200 700",
  event_filtering: "700 400",
  excel_import: "400 150",
  excel_export: "400 150",
  git: "900 200",
  google_earth_export: "700 200",
  import_jobs: "500 400",
  instance_deletion: "400 130",
  librenms: "700 250",
  link: "700 400",
  link_filtering: "700 600",
  log_filtering: "700 350",
  notifications: "1100 400",
  netbox: "700 250",
  opennms: "700 300",
  pool: "800 600",
  pool_filtering: "700 500",
  pool_objects: "700 550",
  service_results: "1200 700",
  server: "600 250",
  server_filtering: "700 450",
  service: "1000 600",
  service_filtering: "1000 600",
  ssh: "700 200",
  task: "900 500",
  task_filtering: "900 650",
  user: "600 300",
  user_filtering: "700 250",
  view: "700 300",
  workflow: "1000 600",
  workflow_filtering: "1000 600",
  workflow_results: "1200 700",
};

const panelName = {
  add_jobs: "Add jobs",
  configuration: "Configuration",
  configuration_filtering: "Configuration Filtering",
  connection: "Connect to device",
  database_deletion: "Database Deletion",
  database_migration: "Database Migration",
  device_filtering: "Device Filtering",
  event_filtering: "Event Filtering",
  excel_export: "Export Topology as an Excel file",
  import_jobs: "Import Jobs",
  server_filtering: "Server Filtering",
  link_filtering: "Link Filtering",
  changelog_filtering: "Changelog Filtering",
  pool_filtering: "Pool Filtering",
  service_filtering: "Service Filtering",
  syslog_filtering: "Syslog Filtering",
  task_filtering: "Task Filtering",
  user_filtering: "User Filtering",
  workflow_filtering: "Workflow Filtering",
};

let userIsActive = true;
let topZ = 1000;

// eslint-disable-next-line
function doc(page) {
  let endpoint = {
    administration: "administration/index.html",
    calendar: "events/tasks.html",
    dashboard: "base/introduction.html",
    "table/configuration": "inventory/configuration_management.html",
    "table/device": "inventory/objects.html",
    "table/event": "events/index.html",
    "table/link": "inventory/objects.html",
    "table/syslog": "events/logs.html",
    "table/changelog": "events/logs.html",
    "table/pool": "inventory/pool_management.html",
    "table/run": "services/index.html",
    "table/server": "administration/index.html",
    "table/service": "services/index.html",
    "table/task": "events/tasks.html",
    "table/user": "administration/index.html",
    "table/workflow": "workflows/index.html",
    view: "views/geographical_view.html",
    workflow_builder: "workflows/index.html",
  }[page];
  $("#doc-link").attr("href", `${documentationUrl}${endpoint}`);
}

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (
      !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
      !this.crossDomain
    ) {
      xhr.setRequestHeader("X-CSRFToken", csrf_token);
    }
    if (!settings.url.includes("filtering")) {
      document.body.style.cursor = "progress";
    }
  },
  complete: function() {
    document.body.style.cursor = "default";
  },
});

const loadScript = (source, beforeEl, async = true, defer = true) => {
  return new Promise((resolve, reject) => {
    let script = document.createElement("script");
    const prior = beforeEl || document.getElementsByTagName("script")[0];

    script.async = async;
    script.defer = defer;

    function onloadHander(_, isAbort) {
      if (
        isAbort ||
        !script.readyState ||
        /loaded|complete/.test(script.readyState)
      ) {
        script.onload = null;
        script.onreadystatechange = null;
        script = undefined;

        if (isAbort) {
          reject();
        } else {
          resolve();
        }
      }
    }

    script.onload = onloadHander;
    script.onreadystatechange = onloadHander;

    script.src = source;
    prior.parentNode.insertBefore(script, prior);
  });
};

function detectUserInactivity() {
  let timer;
  window.onload = resetTimer;
  window.onmousemove = resetTimer;
  window.onmousedown = resetTimer;
  window.ontouchstart = resetTimer;
  window.onclick = resetTimer;
  window.onkeypress = resetTimer;
  window.addEventListener("scroll", resetTimer, true);

  function setUserInactive() {
    userIsActive = false;
  }

  function resetTimer() {
    clearTimeout(timer);
    userIsActive = true;
    timer = setTimeout(setUserInactive, 180000);
  }
}

// eslint-disable-next-line
function openUrl(url) {
  let win = window.open(url, "_blank");
  win.focus();
}

function processResults(callback, results) {
  if (results === false) {
    alertify.notify("HTTP Error 403 – Forbidden", "error", 5);
  } else if (results && results.error) {
    alertify.notify(results.error, "error", 5);
  } else if (results && results.invalid_form) {
    for (const [field, error] of Object.entries(results.errors)) {
      alertify.notify(`Wrong input for "${field}": ${error}`, "error", 20);
    }
  } else {
    callback(results);
  }
}

function call(url, callback) {
  $.ajax({
    type: "POST",
    url: url,
    success: function(results) {
      processResults(callback, results);
    },
  });
}

function fCall(url, form, callback) {
  $.ajax({
    type: "POST",
    url: url,
    data: $(form).serialize(),
    success: function(results) {
      processResults(callback, results);
    },
  });
}

function serializeForm(form) {
  const data = JSON.parse(JSON.stringify($(form).serializeArray()));
  let result = {};
  data.forEach((property) => {
    if (relations.includes(property.name)) {
      if (!(property.name in result)) result[property.name] = [];
      result[property.name].push(property.value);
    } else {
      result[property.name] = property.value;
    }
  });
  return result;
}

// eslint-disable-next-line
function deleteInstance(type, id) {
  call(`/delete_instance/${type}/${id}`, function(result) {
    $(`#instance_deletion-${id}`).remove();
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

// eslint-disable-next-line
function createPanel(name, title, id, processing, type, duplicate) {
  const panelId = id ? `${name}-${id}` : name;
  if ($(`#${panelId}`).length) {
    $(`#${panelId}`).css("zIndex", ++topZ);
    return;
  }
  const isFilteringPanel = panelId.includes("filtering");
  return jsPanel.create({
    id: panelId,
    border: "2px solid #2A3F52",
    theme: "light filledlight",
    headerLogo: "../static/images/logo.png",
    contentOverflow: "hidden scroll",
    contentSize: panelSize[name] || "1000 600",
    position: "center-top 0 10",
    headerTitle: title,
    contentAjax: {
      url: `../form/${name}`,
      done: function(panel) {
        panel.content.innerHTML = this.responseText;
        configureForm(name);
        preprocessForm(panel, id, type, duplicate);
        if (processing) processing(panel);
      },
    },
    dragit: {
      opacity: 0.6,
      containment: 0,
    },
    resizeit: {
      containment: 0,
    },
    onbeforeclose: function(panel, status) {
      if (isFilteringPanel) panel.minimize();
      return !isFilteringPanel;
    },
    setStatus: isFilteringPanel ? "minimized" : "normalized",
  });
}

// eslint-disable-next-line
function showPanel(type, id, processing) {
  return createPanel(type, panelName[type] || type, id, processing);
}

// eslint-disable-next-line
function showFilteringPanel() {
  filteringPanel.normalize();
}

// eslint-disable-next-line
function showDeletionPanel(type, id, name) {
  createPanel("instance_deletion", `Delete ${name}`, id, () => {}, type);
}

function preprocessForm(panel, id, type, duplicate) {
  panel.querySelectorAll(".add-id").forEach((el) => {
    if (duplicate && ["name", "id"].includes(el.name)) return;
    if (id) $(el).prop("id", `${$(el).attr("id")}-${id}`);
  });
  panel.querySelectorAll(".btn-id").forEach((el) => {
    if (id) {
      $(el).attr(
        "onclick",
        type ? `${el.value}("${type}", ${id})` : `${el.value}(${id})`
      );
    } else {
      $(el).attr("onclick", type ? `${el.value}("${type}")` : `${el.value}()`);
    }
  });
}

function configureForm(form, id) {
  if (!formProperties[form]) return;
  for (const [property, type] of Object.entries(formProperties[form])) {
    let el = $(id ? `#${form}-${property}-${id}` : `#${form}-${property}`);
    if (!el.length) el = $(`#${property}`);
    if (type == "date") {
      el.datetimepicker({
        format: "DD/MM/YYYY HH:mm:ss",
        widgetPositioning: {
          horizontal: "left",
          vertical: "bottom",
        },
        useCurrent: false,
      });
    } else {
      const elClass = el.attr("class");
      el.selectpicker({
        liveSearch: elClass ? !elClass.includes("no-search") : false,
        actionsBox: true,
        selectedTextFormat: "count > 3",
      });
    }
  }
}

// eslint-disable-next-line
function showTypePanel(type, id, mode) {
  if (type == "Workflow") type = "workflow";
  createPanel(
    type,
    "",
    id,
    function(panel) {
      if (type == "workflow" || type.includes("Service")) {
        panelCode(type, id, mode);
      }
      if (id) {
        const properties = type === "pool" ? "_properties" : "";
        call(`/get${properties}/${type}/${id}`, function(instance) {
          const title = mode == "duplicate" ? "Duplicate" : "Edit";
          panel.setHeaderTitle(`${title} ${type} - ${instance.name}`);
          processInstance(type, instance);
          if (type == "workflow" && mode == "duplicate") {
            $(`#workflow-btn-${id}`).attr(
              "onclick",
              `duplicateWorkflow(${id})`
            );
          }
          console.log(type);
          if (type === "workflow") {
            $(`#workflow-use_workflow_devices-${id}`).change(function() {
              let isChecked = $(this).is(":checked");
              if (!isChecked) $(`#workflow-traversal_mode-${id}`).val("service");
              $(`#workflow-traversal_mode-${id}`).prop("disabled", !isChecked);
              $(`#workflow-traversal_mode-${id}`).selectpicker("refresh");
            });
            $(`#workflow-use_workflow_devices-${id}`).trigger("change");
          }
          if (type == "workflow" && mode == "run") {
            workflowRunMode(instance);
          }
        });
      } else {
        panel.setHeaderTitle(`Create a New ${type}`);
      }
      if (type.includes("Service")) {
        loadScript(`../static/services/${type}.js`).then(() => {
          try {
            job(id);
          } catch (e) {
            alertify.notify("Failed to load script", "error", 5);
          }
        });
      }
    },
    type,
    mode == "duplicate"
  );
}

function updateProperty(el, property, value, type) {
  const propertyType = formProperties[type][property] || "str";
  if (propertyType.includes("bool") || property.includes("regex")) {
    el.prop("checked", value);
  } else if (propertyType.includes("dict") || propertyType == "json") {
    el.val(value ? JSON.stringify(value) : "{}");
  } else if (
    ["list", "multiselect", "object", "object-list"].includes(propertyType)
  ) {
    try {
      el.selectpicker("deselectAll");
    } catch (e) {
      // ignore
    }
    el.selectpicker(
      "val",
      propertyType === "object"
        ? value.id
        : propertyType === "object-list"
        ? value.map((p) => p.id)
        : value
    );
    el.selectpicker("render");
  } else {
    el.val(value);
  }
}

function processInstance(type, instance) {
  for (const [property, value] of Object.entries(instance)) {
    const el = $(
      instance ? `#${type}-${property}-${instance.id}` : `#${type}-${property}`
    );
    updateProperty(el, property, value, type);
  }
}

// eslint-disable-next-line
function processData(type, id) {
  if (type.includes("Service") || type === "workflow") {
    $(`#${type}-workflows-${id} option`).prop("disabled", false);
    $(`#workflow-traversal_mode-${id}`).prop("disabled", false);
  }
  fCall(
    `/update/${type}`,
    id ? `#edit-${type}-form-${id}` : `#edit-${type}-form`,
    (instance) => {
      if (typeof table != "undefined") table.ajax.reload(null, false);
      $(id ? `#${type}-${id}` : `#${type}`).remove();
      if (type.includes("Service")) saveService(instance, id);
      if (type == "WorkflowEdge" && page == "workflow_builder") {
        saveWorkflowEdge(instance);
      }
      if (type === "workflow" && !id) saveWorkflow(instance);
      alertify.notify(
        `${type.toUpperCase()} ${instance.name ? `'${instance.name}' ` : ""}${
          id ? "updated" : "created"
        }.`,
        "success",
        5
      );
    }
  );
}

// eslint-disable-next-line
function createSearchHeaders() {
  properties.forEach((property) => {
    if (!filteringProperties.includes(property)) return;
    $(`#search-${property}`).on("keyup change", function() {
      $(`#${type}_filtering-${property}`).val($(this).val());
      table.ajax.reload(null, false);
    });
  });
}

// eslint-disable-next-line
function initTable(type) {
  const filteringPanel = showPanel(`${type}_filtering`);
  createSearchHeaders();
  // eslint-disable-next-line new-cap
  const table = $("#table").DataTable({
    serverSide: true,
    orderCellsTop: true,
    scrollX: true,
    fnDrawCallback: () => {
      $(".paginate_button > a").on("focus", function() {
        $(this).blur();
      });
    },
    sDom: "<'top'i>rt<'bottom'lp><'clear'>",
    ajax: {
      url: `/filtering/${type}`,
      type: "POST",
      data: (d) => {
        d.form = serializeForm(`#${type}_filtering-form`);
      },
    },
  });
  if (["changelog", "syslog", "run"].includes(type)) {
    table.order([0, "desc"]).draw();
  }
  return [table, filteringPanel];
}

// eslint-disable-next-line
function filter(formType) {
  table.ajax.reload(null, false);
  alertify.notify("Filter applied.", "success", 5);
}

// eslint-disable-next-line
function undoFilter(formType) {
  $(`#${formType}-form`)[0].reset();
  filteringPanel.minimize();
  table.ajax.reload(null, false);
  alertify.notify("Filter removed.", "success", 5);
}

// eslint-disable-next-line
function refreshTable(interval) {
  if (userIsActive) table.ajax.reload(null, false);
  setTimeout(() => refreshTable(interval), interval);
}

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

(function($, window) {
  $.fn.contextMenu = function(settings) {
    return this.each(function() {
      $(this).on("contextmenu", function(e) {
        if (e.ctrlKey) {
          return;
        }
        const $menu = $(settings.menuSelector)
          .data("invokedOn", $(e.target))
          .show()
          .css({
            position: "absolute",
            left: getMenuPosition(e.clientX, "width", "scrollLeft"),
            top: getMenuPosition(e.clientY, "height", "scrollTop"),
          })
          .off("click")
          .on("click", "a", function(e) {
            $menu.hide();
            const $invokedOn = $menu.data("invokedOn");
            const $selectedMenu = $(e.target);
            settings.menuSelected.call(this, $invokedOn, $selectedMenu);
          });
        return false;
      });
      $("body").click(function() {
        $(settings.menuSelector).hide();
      });
    });

    function getMenuPosition(mouse, direction, scrollDir) {
      const win = $(window)[direction]();
      const scroll = $(window)[scrollDir]();
      const menu = $(settings.menuSelector)[direction]();
      let position = mouse + scroll;
      if (mouse + menu > win && menu < mouse) {
        position -= menu;
      }
      return position;
    }
  };
})(jQuery, window);

$(".dropdown-submenu a.menu-submenu").on("click", function(e) {
  $(this)
    .next("ul")
    .toggle();
  e.stopPropagation();
  e.preventDefault();
});

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
  detectUserInactivity();
});
