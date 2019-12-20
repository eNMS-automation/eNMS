/*
global
alertify: false
CodeMirror: false
config: true
creationMode: true
csrf_token: false
Dropzone: false
formProperties: false
job: false
jsPanel: false
NProgress: false
page: false
processWorkflowData: false
Promise: false
relations: false
relationships: false
tableProperties: false
workflow: true
*/

import models from "./models.js";

let editors = {};
export let tables = {};
export let userIsActive = true;
let topZ = 1000;

const panelSize = {
  add_services: "800 700",
  calendar: "1200 650",
  changelog: "700 300",
  changelog_filtering: "700 300",
  compare: "auto 700",
  configuration: "800 auto",
  database_deletion: "700 400",
  database_migration: "700 300",
  device_connection: "400 500",
  device_results: "1200 700",
  display: "700 700",
  display_configuration: "1200 800",
  event_filtering: "700 400",
  excel_import: "400 150",
  excel_export: "400 150",
  git: "900 200",
  import_service: "500 400",
  instance_deletion: "400 130",
  link_filtering: "700 600",
  logs: "1200 500",
  log_filtering: "700 350",
  notifications: "1100 400",
  pool: "800 600",
  pool_filtering: "1000 700",
  pool_objects: "700 550",
  result_table: "1200 700",
  service_results: "1200 700",
  server: "600 250",
  server_filtering: "700 450",
  ssh: "700 200",
  task: "900 600",
  task_filtering: "900 650",
  user: "600 300",
  user_filtering: "700 250",
  view: "700 300",
  workflow_results: "1200 700",
};

const panelName = {
  add_services: "Add services",
  configuration: "Configuration",
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
  task_filtering: "Task Filtering",
  user_filtering: "User Filtering",
  workflow_filtering: "Workflow Filtering",
};

export function detectUserInactivity() {
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

const panelThemes = {
  logs: { bgContent: "#1B1B1B" },
  device_data: { bgContent: "#1B1B1B" },
  file: { bgContent: "#1B1B1B" },
};

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

// eslint-disable-next-line
export function openUrl(url) {
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
  } else if (results && results.alert) {
    if (Array.isArray(results.alert)) {
      results.alert.map((e) => alertify.notify(e, "error", 5));
    } else {
      alertify.notify(results.alert, "error", 5);
    }
  } else if (results && results.invalid_form) {
    for (const [field, error] of Object.entries(results.errors)) {
      alertify.notify(`Wrong input for "${field}": ${error}`, "error", 20);
    }
  } else {
    if (callback) callback(results);
  }
}

export function call(url, callback) {
  $.ajax({
    type: "POST",
    url: url,
    success: function(results) {
      processResults(callback, results);
    },
  });
}

export function fCall(url, form, callback) {
  $.ajax({
    type: "POST",
    url: url,
    data: $(`[id="${form}"]`).serialize(),
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
    $(`#instance_deletion-${id}`).remove();
    if (type.includes("service") || type == "workflow") type = "service";
    tables[type]
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

export function createTooltips() {
  $("[data-tooltip]").each(function() {
    jsPanel.tooltip.create({
      id: `tooltip-${$(this)
        .attr("data-tooltip")
        .replace(/\s/g, "")}`,
      content: `<p style="margin-right: 10px; margin-left: 10px; color: black">
        <b>${$(this).attr("data-tooltip")}</b></p>`,
      contentSize: "auto",
      connector: true,
      delay: 800,
      header: false,
      position: {
        my: "center-bottom",
        at: "center-top",
        of: this,
      },
      target: this,
      theme: "primary filledlight",
    });
  });
}

export function createPanel(name, title, id, processing, type, duplicate) {
  const panelId = id ? `${name}-${id}` : name;
  if ($(`#${panelId}`).length) {
    $(`#${panelId}`).css("zIndex", ++topZ);
    return;
  }
  return jsPanel.create({
    container: "#container-body",
    id: panelId,
    border: "2px solid #2A3F52",
    theme: panelThemes[name] || "light filledlight",
    headerLogo: "../static/images/logo.png",
    contentOverflow: "hidden scroll",
    contentSize: panelSize[name] || "800 600",
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
export function showPanel(type, id, processing) {
  return createPanel(type, panelName[type] || type, id, processing);
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
    if (duplicate) {
      const property =
        type.includes("service") || type == "workflow" ? "scoped_name" : "name";
      if ([property, "id"].includes(el.name)) return;
    }
    if (id) $(el).prop("id", `${$(el).attr("id")}-${id}`);
  });
  panel.querySelectorAll(".btn-id").forEach((el) => {
    if (id) {
      $(el).attr(
        "onclick",
        type ? `${el.value}("${type}", "${id}")` : `${el.value}("${id}")`
      );
    } else {
      $(el).attr("onclick", type ? `${el.value}("${type}")` : `${el.value}()`);
    }
  });
  panel.querySelectorAll(".doc-link").forEach((el) => {
    $(el).attr("href", `${config.app.documentation_url}${$(el).attr("href")}`);
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
      contentType: "application/json",
      data: function(params) {
        return JSON.stringify({
          term: params.term || "",
          page: params.page || 1,
        });
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

export function configureForm(form, id, panelId) {
  console.log(formProperties[form]);
  if (!formProperties[form]) return;
  for (const [property, field] of Object.entries(formProperties[form])) {
    const fieldId = id ? `${form}-${property}-${id}` : `${form}-${property}`;
    let el = $(`#${fieldId}`);
    if (!el.length) el = $(`#${property}`);
    if (field.type == "date") {
      el.datetimepicker({
        format: "DD/MM/YYYY HH:mm:ss",
        widgetPositioning: {
          horizontal: "left",
          vertical: "bottom",
        },
        useCurrent: false,
      });
    } else if (["list", "multiselect"].includes(field.type)) {
      const elClass = el.attr("class");
      el.selectpicker({
        liveSearch: elClass ? !elClass.includes("no-search") : false,
        actionsBox: true,
        selectedTextFormat: "count > 3",
      });
    } else if (field.type == "code") {
      let editor = CodeMirror.fromTextArea(el[0], {
        lineWrapping: true,
        lineNumbers: true,
        extraKeys: { "Ctrl-F": "findPersistent" },
        matchBrackets: true,
        mode: "python",
        scrollbarStyle: "overlay",
      });
      editor.on("change", () => editor.save());
      if (!editors[id]) editors[id] = {};
      editors[id][property] = editor;
    } else if (["object", "object-list"].includes(field.type)) {
      let model;
      if (relationships[form]) {
        model = relationships[form][property].model;
      } else {
        model = field.model;
      }
      initSelect(el, model, panelId, field.type == "object");
    }
  }
}

function showServicePanel(type, id, mode) {
  const typeInput = $(id ? `#${type}-class-${id}` : `#${type}-class`);
  typeInput.val(type).prop("disabled", true);
  $(id ? `#${type}-name-${id}` : `#${type}-name`).prop("disabled", true);
  if (id) {
    $(`#${type}-shared-${id}`).prop("disabled", true);
    if (mode == "duplicate" && type == "workflow") {
      $(`#original-${id}`).val(id);
    }
  }
  $(id ? `#${type}-workflows-${id}` : `#${type}-workflows`).prop(
    "disabled",
    true
  );
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard({
    enableAllSteps: true,
    keyNavigation: false,
    transitionEffect: "none",
    onShowStep: function() {
      Object.keys(editors[id]).forEach(function(field) {
        editors[id][field].refresh();
      });
    },
  });
  $(".buttonFinish,.buttonNext,.buttonPrevious").hide();
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard("fixHeight");
  if (mode == "run") {
    $(`#${type}-btn-${id}`)
      .removeClass("btn-success")
      .addClass("btn-primary")
      .attr("onclick", `parameterizedRun('${type}', ${id})`)
      .text("Run");
    $(".readonly-when-run").prop("readonly", true);
  }
}

// eslint-disable-next-line
export function showTypePanel(type, id, mode) {
  createPanel(
    type,
    "",
    id,
    function(panel) {
      if (type == "workflow" || type.includes("service")) {
        showServicePanel(type, id, mode);
      }
      if (id) {
        const properties = type === "pool" ? "_properties" : "";
        call(`/get${properties}/${type}/${id}`, function(instance) {
          const action = mode ? mode.toUpperCase() : "EDIT";
          panel.setHeaderTitle(`${action} ${type} - ${instance.name}`);
          processInstance(type, instance);
        });
      } else {
        panel.setHeaderTitle(`Create a New ${type}`);
        if (page == "workflow_builder" && creationMode == "create_service") {
          $(`#${type}-workflows`).append(
            new Option(workflow.name, workflow.id)
          );
          $(`#${type}-workflows`)
            .val(workflow.id)
            .trigger("change");
        }
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

function updateProperty(instance, el, property, value, type) {
  let propertyType;
  if (formProperties[type][property]) {
    propertyType = formProperties[type][property].type;
  } else {
    propertyType = "str";
  }
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
  } else if (propertyType == "code") {
    const editor = editors[instance.id][property];
    if (editor) editor.setValue(value);
  } else if (propertyType == "field-list") {
    for (let [index, form] of value.entries()) {
      for (const [key, value] of Object.entries(form)) {
        $(`#${type}-${property}-${index}-${key}-${instance.id}`).val(value);
      }
    }
  } else {
    el.val(value);
  }
}

function processInstance(type, instance) {
  for (const [property, value] of Object.entries(instance)) {
    const el = $(
      instance ? `#${type}-${property}-${instance.id}` : `#${type}-${property}`
    );
    updateProperty(instance, el, property, value, type);
  }
}

// eslint-disable-next-line
export function processData(type, id) {
  if (type.includes("service") || type == "workflow") {
    $(id ? `#${type}-workflows-${id}` : `#${type}-workflows`).prop(
      "disabled",
      false
    );
    if (id) $(`#${type}-shared-${id}`).prop("disabled", false);
  }
  fCall(
    `/update/${type}`,
    id ? `edit-${type}-form-${id}` : `edit-${type}-form`,
    (instance) => {
      const tableType =
        type.includes("service") || type == "workflow" ? "service" : type;
      if (page.includes("table")) tables[tableType].ajax.reload(null, false);
      $(id ? `#${type}-${id}` : `#${type}`).remove();
      if (page == "workflow_builder") processWorkflowData(instance, id);
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

export function initTable(type, instance, runtime, id) {
  // eslint-disable-next-line new-cap
  tables[type] = $(id ? `#table-${id}` : "#table").DataTable({
    serverSide: true,
    orderCellsTop: true,
    autoWidth: false,
    scrollX: true,
    drawCallback: function() {
      $(".paginate_button > a").on("focus", function() {
        $(this).blur();
      });
      createTooltips();
      adjustHeight();
    },
    sDom: "<'top'i>rt<'bottom'lp><'clear'>",
    columns: models[type].columns,
    columnDefs: [{ className: "dt-center", targets: "_all" }],
    initComplete: function() {
      this.api()
        .columns()
        .every(function(index) {
          const data = models[type].columns[index];
          let element;
          if (data.search == "text") {
            element = `
              <input
                id="${type}_filtering-${data.data}"
                name="${data.data}"
                type="text"
                placeholder="&#xF002;"
                class="form-control"
                style="font-family:Arial, FontAwesome; width: 100%; height: 30px; margin-top: 5px"
              >`;
          } else if (data.search == "bool") {
            element = `
              <select
                id="${type}_filtering-${data.data}"
                name="${data.data}"
                class="form-control"
                style="width: 100%; height: 30px; margin-top: 5px"
              >
                <option value="">Any</option>
                <option value="bool-true">True</option>
                <option value="bool-false">False</option>
              </select>`;
          } else if (data.data == "buttons") {
            element = models[type].controls.join("");
          }
          $(element)
            .appendTo($(this.header()))
            .on("keyup change", function() {
              tables[type].ajax.reload(null, false);
            })
            .on("click", function(e) {
              e.stopPropagation();
            });
        });
      this.api().columns.adjust();
      adjustHeight();
    },
    ajax: {
      url: `/table_filtering/${type}`,
      type: "POST",
      contentType: "application/json",
      data: (d) => {
        const form = $(`#${type}_filtering`).length
          ? `#${type}_filtering-form`
          : `#search-${type}-form`;
        d.form = serializeForm(form);
        d.instance = instance;
        if (runtime) {
          d.runtime = $(`#runtimes-${instance.id}`).val() || runtime;
        }
        return JSON.stringify(d);
      },
      dataSrc: function(result) {
        return result.data.map((instance) => new models[type](instance));
      },
    },
  });
  if (["changelog", "run", "result"].includes(type)) {
    tables[type].order([0, "desc"]).draw();
  }
  if (type == "service") {
    $("#parent-filtering").on("change", function() {
      tables["service"].ajax.reload(null, false);
    });
  }
  if (["run", "service", "task", "workflow"].includes(type)) {
    refreshTablePeriodically(type, 3000);
  }
}

export function filterTable(formType) {
  tables[formType].ajax.reload(null, false);
  alertify.notify("Filter applied.", "success", 5);
}

export function refreshTable(tableType, displayNotification) {
  tables[tableType].ajax.reload(null, false);
  if (displayNotification) alertify.notify("Table refreshed.", "success", 5);
}

function refreshTablePeriodically(tableType, interval) {
  if (userIsActive) refreshTable(tableType, false);
  setTimeout(() => refreshTablePeriodically(tableType, interval), interval);
}

(function($, jstree, undefined) {
  "use strict";

  $.jstree.plugins.html_row = function(options, parent) {
    // eslint-disable-next-line
    this.redraw_node = function(nodeId, ...args) {
      let el = parent.redraw_node.apply(this, [nodeId, ...args]);
      if (el) {
        let node = this._model.data[nodeId];
        this.settings.html_row.default(el, node);
      }
      return el;
    };
  };
})(jQuery);

export function copyToClipboard(text, isId) {
  if (isId) text = $(`#${text}`).val();
  let dummy = document.createElement("textarea");
  document.body.appendChild(dummy);
  dummy.value = text;
  dummy.select();
  document.execCommand("copy");
  document.body.removeChild(dummy);
  alertify.notify(`Copied to Clipboard: ${text}`, "success", 5);
}

export function adjustHeight() {
  const height =
    $("body")[0].scrollHeight > window.innerHeight
      ? document.body.clientHeight
      : window.innerHeight;
  $("#sidebar").css("min-height", height);
  $(".x_panel").css("min-height", height - $(".nav_menu").height() - 30);
  $(".right_col").css("min-height", height - $(".nav_menu").height());
  Object.keys(tables).forEach((table) => tables[table].columns.adjust());
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
