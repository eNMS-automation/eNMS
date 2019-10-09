/*
global
alertify: false
csrf_token: false
documentationUrl: false
filteringProperties: false
formProperties: false
job: false
jsPanel: false
NProgress: false
page: false
panelCode: false
Promise: false
relations: false
relationships: false
saveWorkflow: false
saveWorkflowEdge: false
saveWorkflowService: false
tableProperties: false
workflowRunMode: false
*/

const currentUrl = window.location.href.split("#")[0].split("?")[0];
let tables = {};
let userIsActive = true;
let topZ = 1000;

const panelSize = {
  add_services: "800 500",
  changelog: "700 300",
  changelog_filtering: "700 300",
  cluster: "700 200",
  compare: "1800 800",
  configuration: "1200 700",
  configuration_filtering: "700 600",
  database_deletion: "700 400",
  database_migration: "700 300",
  device: "700 500",
  device_connection: "400 500",
  device_filtering: "700 600",
  device_results: "1200 700",
  display: "700 700",
  display_configuration: "1200 800",
  event_filtering: "700 400",
  excel_import: "400 150",
  excel_export: "400 150",
  git: "900 200",
  google_earth_export: "700 200",
  import_service: "500 400",
  instance_deletion: "400 130",
  librenms: "700 250",
  link: "700 400",
  link_filtering: "700 600",
  log_filtering: "700 350",
  notifications: "1100 400",
  netbox: "700 250",
  opennms: "700 300",
  pool: "800 600",
  pool_filtering: "1000 700",
  pool_objects: "700 550",
  result: "1200 700",
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
  add_services: "Add services",
  configuration: "Configuration",
  configuration_filtering: "Configuration Filtering",
  database_deletion: "Database Deletion",
  database_migration: "Database Migration",
  device_connection: "Connect to device",
  device_filtering: "Device Filtering",
  event_filtering: "Event Filtering",
  excel_export: "Export Topology as an Excel file",
  import_service: "Import Service",
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

// eslint-disable-next-line
function cantorPairing(x, y) {
  return ((x + y) * (x + y + 1)) / 2 + y;
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
      if (property.value) result[property.name] = property.value;
    }
  });
  return result;
}

// eslint-disable-next-line
function deleteInstance(type, id) {
  call(`/delete_instance/${type}/${id}`, function(result) {
    const tableType = type.includes("service") ? "service" : type;
    $(`#instance_deletion-${id}`).remove();
    tables[tableType]
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

function createTooltips() {
  $("[data-tooltip]").each(function() {
    jsPanel.tooltip.create({
      content: `<p style="margin-right: 10px; margin-left: 10px; color: black">
        <b>${$(this).attr("data-tooltip")}</b></p>`,
      contentSize: 'auto',
      connector: true,
      delay: 800,
      header: false,
      position: {
        my: 'center-bottom',
        at: 'center-top',
        of: this
      },
      target: this,
      theme: "primary filledlight",
    });
  });
}

// eslint-disable-next-line
function createPanel(name, title, id, processing, type, duplicate) {
  const panelId = id ? `${name}-${id}` : name;
  if ($(`#${panelId}`).length) {
    $(`#${panelId}`).css("zIndex", ++topZ);
    return;
  }
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
        preprocessForm(panel, id, type, duplicate);
        configureForm(name, id, panelId);
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
  });
}

// eslint-disable-next-line
function showPanel(type, id, processing) {
  return createPanel(type, panelName[type] || type, id, processing);
}

// eslint-disable-next-line
function showFilteringPanel(panelType) {
  showPanel(panelType);
}

// eslint-disable-next-line
function showDeletionPanel(instance) {
  createPanel(
    "instance_deletion",
    `Delete ${instance.name}`,
    instance.id,
    () => {},
    instance.type
  );
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

function initSelect(el, model, parentId, single) {
  el.select2({
    multiple: !single,
    closeOnSelect: single ? true : false,
    dropdownParent: parentId ? $(`#${parentId}`) : $(document.body),
    ajax: {
      url: `/multiselect_filtering/${model}`,
      type: "POST",
      delay: 250,
      data: function(params) {
        return {
          term: params.term || "",
          page: params.page || 1,
        };
      },
      processResults: function(data, params) {
        params.page = params.page || 1;
        return {
          results: data.items,
          pagination: {
            more: params.page * 10 < data.total_count,
          },
        };
      },
    },
  });
}

function configureForm(form, id, panelId) {
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
    } else if (["list", "multiselect"].includes(type)) {
      const elClass = el.attr("class");
      el.selectpicker({
        liveSearch: elClass ? !elClass.includes("no-search") : false,
        actionsBox: true,
        selectedTextFormat: "count > 3",
      });
    } else if (["object", "object-list"].includes(type)) {
      let model;
      if (relationships[form]) {
        model = relationships[form][property].model;
      } else {
        model = property.substring(0, property.length - 1);
      }
      initSelect(el, model, panelId, type == "object");
    }
  }
}

// eslint-disable-next-line
function showTypePanel(type, id, mode) {
  createPanel(
    type,
    "",
    id,
    function(panel) {
      if (type == "workflow" || type.includes("service")) {
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
          if (type == "workflow" && mode == "run") {
            workflowRunMode(instance);
          }
        });
      } else {
        panel.setHeaderTitle(`Create a New ${type}`);
      }
      if (type.includes("service")) {
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
  if (propertyType.includes("bool")) {
    el.prop("checked", value);
  } else if (propertyType.includes("dict") || propertyType == "json") {
    el.val(value ? JSON.stringify(value) : "{}");
  } else if (["list", "multiselect"].includes(propertyType)) {
    try {
      el.selectpicker("deselectAll");
    } catch (e) {
      // ignore
    }
    el.selectpicker("val", value);
    el.selectpicker("render");
  } else if (propertyType == "object-list") {
    value.forEach((o) => el.append(new Option(o.name, o.id)));
    el.val(value.map((p) => p.id)).trigger("change");
  } else if (propertyType == "object") {
    el.append(new Option(value.name, value.id))
      .val(value.id)
      .trigger("change");
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
  fCall(
    `/update/${type}`,
    id ? `#edit-${type}-form-${id}` : `#edit-${type}-form`,
    (instance) => {
      const tableType = type.includes("service") || type == "workflow" ? "service" : type;
      if (page.includes("table")) tables[tableType].ajax.reload(null, false);
      $(id ? `#${type}-${id}` : `#${type}`).remove();
      if (page == "workflow_builder") {
        if (type == "workflow_edge") saveWorkflowEdge(instance);
        if (type.includes("service")) saveWorkflowService(instance, id);
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
function createSearchHeaders(type) {
  tableProperties[type || "result"].forEach((property) => {
    if (!filteringProperties[type || "result"].includes(property)) return;
    $(`#${type}_filtering-${property}`).on("keyup change", function() {
      tables[type].ajax.reload(null, false);
    });
  });
}

// eslint-disable-next-line
function initTable(type, instance, runtime) {
  // eslint-disable-next-line new-cap
  tables[type] = $(`#${type}-table`).DataTable({
    serverSide: true,
    orderCellsTop: true,
    autoWidth: false,
    scrollX: true,
    fnDrawCallback: () => {
      $(".paginate_button > a").on("focus", function() {
        $(this).blur();
      });
      createTooltips();
    },
    sDom: "<'top'i>rt<'bottom'lp><'clear'>",
    ajax: {
      url: `/table_filtering/${type}`,
      type: "POST",
      data: (d) => {
        const form = $(`#${type}_filtering`).length
          ? `#${type}_filtering-form`
          : `#search-${type}-form`;
        d.form = serializeForm(form);
        d.instance = instance;
        d.runtime = runtime;
      },
    },
  });
  createSearchHeaders(type);
  if (
    ["changelog", "syslog", "run", "configuration", "result"].includes(type)
  ) {
    tables[type].order([0, "desc"]).draw();
  }
  if (["run", "service", "task", "workflow"].includes(type)) {
    refreshTablePeriodically(type, 3000);
  }
}

// eslint-disable-next-line
function filter(formType) {
  tables[formType].ajax.reload(null, false);
  alertify.notify("Filter applied.", "success", 5);
}

// eslint-disable-next-line
function refreshTable(tableType, displayNotification) {
  tables[tableType].ajax.reload(null, false);
  if (displayNotification) alertify.notify("Table refreshed.", "success", 5);
}

// eslint-disable-next-line
function refreshTablePeriodically(tableType, interval) {
  if (userIsActive) refreshTable(tableType, false);
  setTimeout(() => refreshTablePeriodically(tableType, interval), interval);
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
      $("#eNMS").css({ "font-size": "20px" });
      $("#eNMS-version").css({ "font-size": "15px" });
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
      $("#eNMS").css({ "font-size": "30px" });
      $("#eNMS-version").css({ "font-size": "20px" });
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
  if (page.includes("table")) initTable(page.split("/")[1]);
  configureForm(page);
  doc(page);
  detectUserInactivity();
  createTooltips();
});
