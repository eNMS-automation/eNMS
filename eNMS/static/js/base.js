/*
global
alertify: false
CodeMirror: false
settings: true
csrf_token: false
eNMS: true
formProperties: false
job: false
jsPanel: false
JSONEditor: false
moment: false
page: false
relations: false
relationships: false
user: false
*/

import { tableInstances } from "./table.js";
import { creationMode, processWorkflowData, workflow } from "./workflow.js";

export let editors = {};
export let jsonEditors = {};
export let userIsActive = true;
let topZ = 1000;

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
  beforeSend: function (xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrf_token);
    }
    if (!settings.url.includes("filtering")) {
      document.body.style.cursor = "progress";
    }
  },
  complete: function () {
    document.body.style.cursor = "default";
  },
});

function loadScript(url, id) {
  let script = document.createElement("script");
  script.onload = function () {
    try {
      job(id);
    } catch (e) {
      notify("Failed to load script", "error", 5);
    }
  };
  script.src = url;
  document.head.appendChild(script);
}

export function openUrl(url) {
  let win = window.open(url, "_blank");
  win.focus();
}

export function cantorPairing(x, y) {
  return ((x + y) * (x + y + 1)) / 2 + y;
}

function processResults(callback, results) {
  if (results === false) {
    notify("HTTP Error 403 – Forbidden", "error", 5);
  } else if (results && results.alert) {
    if (Array.isArray(results.alert)) {
      results.alert.map((e) => notify(e, "error", 5, true));
    } else {
      notify(results.alert, "error", 5, true);
    }
  } else if (results && results.invalid_form) {
    for (const [field, error] of Object.entries(results.errors)) {
      notify(`Wrong input for "${field}": ${error}`, "error", 20);
    }
  } else {
    if (callback) callback(results);
  }
}

export const call = function ({ url, data, form, callback }) {
  let params = {
    type: "POST",
    url: url,
    success: function (results) {
      processResults(callback, results);
    },
    error: function (error) {
      let message = `Error ${error.status}: ${error.statusText}.`;
      if (error.status == 400) {
        message += " Your session might have expired, try refreshing the page.";
      }
      notify(message, "error", 5);
    },
  };
  if (data) {
    Object.assign(params, {
      data: JSON.stringify(data),
      contentType: "application/json",
      dataType: "json",
    });
  } else if (form) {
    params.data = $(`[id="${form}"]`).serialize();
  }
  $.ajax(params);
};

export function serializeForm(form) {
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

export const deleteInstance = function (type, id) {
  call({
    url: `/delete_instance/${type}/${id}`,
    callback: function (result) {
      $(`#instance_deletion-${id}`).remove();
      if (type.includes("service") || type == "workflow") {
        type = "service";
        const path = localStorage.getItem("path");
        if (path && path.includes(id)) {
          localStorage.removeItem("path");
        }
      }
      tableInstances[type].table
        .row($(`#${id}`))
        .remove()
        .draw(false);
      const name = result.name ? `'${result.name}'` : "";
      notify(`${type.toUpperCase()} ${name} deleted.`, "success", 5, true);
    },
  });
};

export function downloadFile(name, content, type) {
  let link = document.createElement("a");
  link.setAttribute(
    "href",
    window.URL.createObjectURL(
      new Blob([content], {
        type: type == "csv" ? "text/csv" : "text/plain",
      })
    )
  );
  link.setAttribute(
    "download",
    `${name}_${new Date().toLocaleString("en-US")}.${type}`
  );
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export function createTooltips() {
  $("[data-tooltip]").each(function () {
    jsPanel.tooltip.create({
      id: `tooltip-${$(this).attr("data-tooltip").replace(/\s/g, "")}`,
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

export function openPanel({
  name,
  title,
  id,
  callback,
  type,
  duplicate,
  content,
  size,
  url,
}) {
  if (!user.is_admin && !user.get_requests.includes(url || `/form/${name}`)) {
    return notify("Error 403 - Operation not allowed.", "error", 5);
  }
  const panelId = id ? `${name}-${id}` : name;
  if ($(`#${panelId}`).length) {
    $(`#${panelId}`).css("zIndex", ++topZ);
    return;
  }
  let kwargs = {
    container: ".right_column",
    id: panelId,
    border: "2px solid #2A3F52",
    theme: panelThemes[name] || "light filledlight",
    headerLogo: "../static/img/logo.png",
    contentOverflow: "hidden scroll",
    contentSize: size || {
      width: () => window.innerWidth * 0.5,
      height: () => window.innerHeight * 0.75,
    },
    position: "center-top 0 10",
    headerTitle: title,
    maximizedMargin: 10,
    dragit: {
      opacity: 0.6,
      containment: 0,
    },
    resizeit: {
      containment: 0,
    },
  };
  if (content) {
    kwargs.content = content;
  } else {
    kwargs.contentAjax = {
      url: url || `../form/${name}`,
      done: function (panel) {
        panel.content.innerHTML = this.responseText;
        preprocessForm(panel, id, type, duplicate);
        configureForm(name, id, panelId);
        if (callback) callback(panel);
      },
    };
  }
  const panel = jsPanel.create(kwargs);
  if (callback && content) callback(content);
  $(panel).css({ top: `${50 + $(window).scrollTop()}px`, position: "absolute" });
}

export function createTooltip({
  name,
  target,
  container,
  url,
  persistent,
  position,
  autoshow,
  title,
  content,
  callback,
  size,
}) {
  if ($(target).length) {
    let kwargs = {
      autoshow: autoshow,
      id: `tooltip-${name}`,
      container: container,
      contentSize: size || "auto",
      connector: true,
      delay: 0,
      mode: "sticky",
      position: position,
      target: target,
      ttipEvent: "click",
      theme: "light",
    };
    if (content) {
      kwargs.content = content;
    } else {
      kwargs.contentAjax = {
        url: url,
        done: function (panel) {
          panel.content.innerHTML = this.responseText;
          preprocessForm(panel);
          configureForm(name);
          if (callback) callback(panel);
        },
      };
    }
    if (title) {
      Object.assign(kwargs, { headerTitle: title, headerControls: "closeonly" });
    } else {
      kwargs.header = false;
    }
    if (persistent) {
      kwargs.onbeforeclose = function () {
        $(this).hide();
      };
    }
    jsPanel.tooltip.create(kwargs);
    if (persistent) {
      $(target).on("click", function () {
        $(`#tooltip-${name}`).show();
      });
    }
  }
}

export function showDeletionPanel(instance) {
  openPanel({
    name: "instance_deletion",
    content: `
      <div class="modal-body">
        Are you sure you want to permanently remove this item ?
      </div>
      <div class="modal-footer">
        <center>
          <button
            type="button"
            class="btn btn-danger"
            onclick="eNMS.base.deleteInstance('${instance.type}', ${instance.id})"
          >
            Delete
          </button>
        </center>
      </div><br>`,
    title: `Delete ${instance.name}`,
    size: "auto",
    id: instance.id,
  });
}

export function preprocessForm(panel, id, type, duplicate) {
  if (type) {
    panel.querySelectorAll(".add-type").forEach((el) => {
      $(el).prop("id", `${$(el).attr("id")}-${type}`);
    });
  }
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
    $(el).attr("href", `${settings.app.documentation_url}${$(el).attr("href")}`);
  });
  panel.querySelectorAll("[help]").forEach((el) => {
    const button = $(`
      <button class="icon-button" type="button">
        <span class="glyphicon glyphicon-info-sign"></span>
      </button>
    `).on("click", function () {
      const helpUrl = $(el).attr("help");
      openPanel({
        name: `help-${$(el).attr("for")}`,
        title: $(el).attr("for"),
        size: "600px auto",
        url: helpUrl.charAt(0) === "/" ? `..${helpUrl}` : `../help/${helpUrl}`,
        callback: function (helpPanel) {
          helpPanel.querySelectorAll(".help-snippet").forEach((el) => {
            const editor = CodeMirror.fromTextArea(el, {
              lineNumbers: true,
              readOnly: true,
            });
            editor.setSize("100%", "fit-content");
          });
        },
      });
    });
    $(el).append(button);
  });
}

export function initSelect(el, model, parentId, single) {
  el.select2({
    multiple: !single,
    allowClear: true,
    placeholder: `Select ${single ? `a ${model}` : `${model}s`}`,
    closeOnSelect: single ? true : false,
    dropdownParent: parentId ? $(`#${parentId}`) : $(document.body),
    ajax: {
      url: `/multiselect_filtering/${model}`,
      type: "POST",
      delay: 250,
      contentType: "application/json",
      data: function (params) {
        return JSON.stringify({
          term: params.term || "",
          page: params.page || 1,
        });
      },
      processResults: function (data, params) {
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
    } else if (["list", "multiselect", "multiselect-string"].includes(field.type)) {
      const elClass = el.attr("class");
      el.selectpicker({
        liveSearch: elClass ? !elClass.includes("no-search") : false,
        actionsBox: true,
        selectedTextFormat: "count > 3",
      });
    } else if (field.type == "json") {
      let editor = new JSONEditor(el.next()[0], {
        onChange: function () {
          $(el).val(JSON.stringify(editor.get()));
        },
      });
      $(el).val("{}");
      if (id) {
        if (!jsonEditors[id]) jsonEditors[id] = {};
        jsonEditors[id][property] = editor;
      } else {
        jsonEditors[property] = editor;
      }
    } else if (field.type == "code") {
      let editor = CodeMirror.fromTextArea(el[0], {
        lineWrapping: true,
        lineNumbers: true,
        extraKeys: { "Ctrl-F": "findPersistent" },
        matchBrackets: true,
        mode: "python",
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
    if (mode == "duplicate") {
      $(`#${type}-shared-${id}`).prop("checked", false);
    }
    $(`#${type}-shared-${id}`).prop("disabled", true);
    if (mode == "duplicate" && type == "workflow") {
      $(`#copy-${id}`).val(id);
    }
  }
  $(id ? `#${type}-workflows-${id}` : `#${type}-workflows`).prop("disabled", true);
  $(id ? `#${type}-wizard-${id}` : `#${type}-wizard`).smartWizard({
    enableAllSteps: true,
    keyNavigation: false,
    transitionEffect: "none",
    onShowStep: function () {
      Object.keys(editors[id]).forEach(function (field) {
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
      .attr("onclick", `eNMS.automation.parameterizedRun('${type}', ${id})`)
      .text("Run");
    $(".readonly-when-run").prop("readonly", true);
  }
}

function configureServicePanel(type, id, mode) {
  if (mode == "duplicate") {
    $(`#${type}-shared-${id}`).prop("checked", false);
    $(`#${type}-workflows-${id}`).val([workflow.id]).trigger("change");
  }
}

export function showTypePanel(type, id, mode) {
  openPanel({
    name: type,
    id: id,
    callback: function (panel) {
      if (type == "workflow" || type.includes("service")) {
        showServicePanel(type, id, mode);
      }
      if (id) {
        const properties = type === "pool" ? "_properties" : "";
        call({
          url: `/get${properties}/${type}/${id}`,
          callback: function (instance) {
            const action = mode ? mode.toUpperCase() : "EDIT";
            panel.setHeaderTitle(`${action} ${type} - ${instance.name}`);
            processInstance(type, instance);
            if (type.includes("service") || type == "workflow") {
              configureServicePanel(type, id, mode);
            }
          },
        });
      } else {
        panel.setHeaderTitle(`Create a New ${type}`);
        if (page == "workflow_builder" && creationMode == "create_service") {
          $(`#${type}-workflows`).append(new Option(workflow.name, workflow.id));
          $(`#${type}-workflows`).val(workflow.id).trigger("change");
        }
      }
      if (type.includes("service") || type == "workflow") {
        $(`#${type}-scoped_name`).focus();
        loadScript(`../static/js/services/${type}.js`, id);
      } else {
        $(`#${type}-name`).focus();
      }
    },
    type: type,
    duplicate: mode == "duplicate",
  });
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
  } else if (propertyType.includes("dict")) {
    el.val(value ? JSON.stringify(value) : "{}");
  } else if (["list", "multiselect", "multiselect-string"].includes(propertyType)) {
    try {
      el.selectpicker("deselectAll");
    } catch (e) {
      // ignore
    }
    if (propertyType == "multiselect-string") {
      value = value ? JSON.parse(value.replace(/'/g, `"`)) : [];
    }
    el.selectpicker("val", value);
    el.selectpicker("render");
  } else if (propertyType == "object-list") {
    value.forEach((o) => el.append(new Option(o.name, o.id)));
    el.val(value.map((p) => p.id)).trigger("change");
  } else if (propertyType == "object") {
    el.append(new Option(value.name, value.id)).val(value.id).trigger("change");
  } else if (propertyType == "json") {
    el.val(JSON.stringify(value));
    const editor = jsonEditors[instance.id][property];
    if (editor) editor.set(value);
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

function processData(type, id) {
  if (type.includes("service") || type == "workflow") {
    $(id ? `#${type}-workflows-${id}` : `#${type}-workflows`).prop("disabled", false);
    if (id) $(`#${type}-shared-${id}`).prop("disabled", false);
  }
  call({
    url: `/update/${type}`,
    form: id ? `edit-${type}-form-${id}` : `edit-${type}-form`,
    callback: (instance) => {
      const tableType =
        type.includes("service") || type == "workflow" ? "service" : type;
      if (page.includes("table")) {
        tableInstances[tableType].table.ajax.reload(null, false);
      }
      $(id ? `#${type}-${id}` : `#${type}`).remove();
      if (page == "workflow_builder") processWorkflowData(instance, id);
      notify(
        `${type.toUpperCase()} ${instance.name ? `'${instance.name}' ` : ""}${
          id ? "updated" : "created"
        }.`,
        "success",
        5,
        true
      );
    },
  });
}

(function ($, jstree, undefined) {
  "use strict";

  $.jstree.plugins.html_row = function (options, parent) {
    // eslint-disable-next-line
    this.redraw_node = function (nodeId, ...args) {
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
  notify(`Copied to Clipboard: ${text}`, "success", 5);
}

(function ($, window) {
  $.fn.contextMenu = function (settings) {
    return this.each(function () {
      $(this).on("contextmenu", function (e) {
        if (e.ctrlKey) {
          return;
        }
        const $menu = $(settings.menuSelector)
          .show()
          .css({
            position: "absolute",
            left: getMenuPosition(e.clientX, "width", "scrollLeft"),
            top: getMenuPosition(e.clientY, "height", "scrollTop"),
          })
          .off("click")
          .on("click", "a", function (e) {
            $menu.hide();
            const $selectedMenu = $(e.target);
            settings.menuSelected.call(this, $selectedMenu);
          });
        return false;
      });
      $(".dropdown-submenu a.menu-submenu").on("click", function (e) {
        const isHidden = $(this).next("ul").is(":hidden");
        $(".dropdown-submenu a.menu-submenu").next("ul").hide();
        $(this).next("ul").toggle(isHidden);
        e.stopPropagation();
        e.preventDefault();
      });
      $("body").click(function () {
        $(".dropdown-submenu a.menu-submenu").next("ul").hide();
        $(settings.menuSelector).hide();
      });
    });

    function getMenuPosition(mouse, direction, scrollDir) {
      const win = $(window)[direction]();
      const scroll = $(window)[scrollDir]();
      const menu = $(settings.menuSelector)[direction]();
      const offset =
        direction == "width" ? $(".left_column").width() : $(".header").height() + 2;
      let position = mouse + scroll - offset;
      if (mouse + menu > win && menu < mouse) {
        position -= menu;
      }
      return position;
    }
  };
})(jQuery, window);

export function notify(...args) {
  if (args.length == 4) {
    const alerts = JSON.parse(localStorage.getItem("alerts"));
    localStorage.setItem(
      "alerts",
      JSON.stringify([
        ...alerts,
        [...args.slice(0, -1), moment().format("MMMM Do YYYY, h:mm:ss a")],
      ])
    );
    const alert = alerts.length + 1 > 99 ? "99+" : alerts.length + 1;
    $("#alert-number").text(alert);
  }
  alertify.notify(...args);
}

function showAllAlerts() {
  openPanel({
    name: "alerts_table",
    callback: () => {
      $("#alerts-table")
        // eslint-disable-next-line new-cap
        .DataTable({
          columns: [{ width: "200px" }, { width: "60px" }, null],
        })
        .order([0, "desc"])
        .draw();
    },
    content: `
      <div class="modal-body">
        <table 
          id="alerts-table"
          class="table table-striped table-bordered table-hover wrap"
          style="width:100%"
        >
          <thead>
            <tr>
                <th>Date</th>
                <th>Type</th>
                <th style="word-wrap: break-word">Content</th>
            </tr>
          </thead>
          <tbody>
          ${getAlerts()}
          </tbody>
        </table>
      <div>
    `,
  });
}

function getAlerts(preview) {
  let alerts = JSON.parse(localStorage.getItem("alerts")).reverse();
  if (preview) alerts = alerts.splice(0, 4);
  return alerts
    .map((alert) => {
      if (preview) {
        const color = alert[1] == "error" ? "f87979" : "5BBD72";
        const fontSize = preview ? "11px" : "14px";
        return `
          <li
            style="background: #${color}; pointer-events: none; margin: 2px 6px"
          >
          <a style="word-wrap: break-word; color: #FFFFFF">
          <span class="time" style="font-size: ${fontSize}">
            ${alert[3]}
          </span>
          <span>${alert[0]}</span>
          </a>
        </li>`;
      } else {
        return `
        <tr>
          <td>${alert[3]}</td>
          <td>${alert[1]}</td>
          <td>${alert[0]}</td>
        </tr>`;
      }
    })
    .join("");
}

function clearAlerts() {
  localStorage.setItem("alerts", "[]");
  $("#alert-number").empty();
}

export function createAlerts() {
  $("#alerts").empty().append(`
    ${getAlerts(true)}
    <li style="margin: 3px 6px 0; padding: 10px; margin-bottom: 6px;">
      <div class="text-center">
        <a class="dropdown-item" onclick="eNMS.base.showAllAlerts()">
          <strong>See All Alerts</strong>
          <i class="fa fa-angle-right"></i>
        </a>
      </div>
    </li>
    <li style="margin: 3px 6px 0; padding: 10px; margin-bottom: 6px;">
      <div class="text-center">
        <a class="dropdown-item" onclick="eNMS.base.clearAlerts()">
          <strong>Clear All Alerts</strong>
          <i class="fa fa-remove"></i>
        </a>
      </div>
    </li>
  `);
}

export function configureNamespace(namespace, functions) {
  eNMS[namespace] = {};
  functions.forEach((f) => (eNMS[namespace][f.name] = f));
}

function fullScreen() {
  if (
    document.fullscreenElement ||
    document.webkitFullscreenElement ||
    document.mozFullScreenElement ||
    document.msFullscreenElement
  ) {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.mozCancelFullScreen) {
      document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
  } else {
    const element = document.documentElement;
    if (element.requestFullscreen) {
      element.requestFullscreen();
    } else if (element.mozRequestFullScreen) {
      element.mozRequestFullScreen();
    } else if (element.webkitRequestFullscreen) {
      element.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
    } else if (element.msRequestFullscreen) {
      element.msRequestFullscreen();
    }
  }
}

configureNamespace("base", [
  call,
  clearAlerts,
  copyToClipboard,
  createAlerts,
  deleteInstance,
  fullScreen,
  loadScript,
  openPanel,
  processData,
  processInstance,
  showAllAlerts,
  showDeletionPanel,
  showTypePanel,
]);
