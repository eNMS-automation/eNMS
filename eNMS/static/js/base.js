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
NProgress: false
page: false
parameters: false
rbac: false
relationships: false
subtypes: false
user: false
*/

import {
  folderPath,
  openDebugPanel,
  showCredentialPanel,
  showFolderPanel,
} from "./administration.js";
import { creationMode, initBuilder, instance, processBuilderData } from "./builder.js";
import { initDashboard } from "./inventory.js";
import { refreshTable, tables, tableInstances } from "./table.js";
import { initVisualization } from "./visualization.js";
import { showLinkPanel, showNodePanel, updateNetworkPanel } from "./networkBuilder.js";
import { showServicePanel } from "./workflowBuilder.js";

const currentUrl = `${location.origin}/${page}`;
const pageHistory = ["workflow_builder", "service_table", "network_table"];
export let editors = {};
export let history = pageHistory.includes(page) ? [""] : [];
export let historyPosition = page.includes("table") ? 0 : -1;
export let jsonEditors = {};
export let userIsActive = true;

let currentTheme = user.theme;
let topZ = 1000;
let triggerMenu = true;

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
  "report-text": { bgContent: "#1B1B1B" },
  logs: { bgContent: "#1B1B1B" },
  device_data: { bgContent: "#1B1B1B" },
  file_editor: { bgContent: "#1B1B1B" },
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
    notify("Error 403 - Not Authorized.", "error", 5);
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

export function observeMutations(container, target, callback) {
  new (window.MutationObserver || window.WebKitMutationObserver)((mutations) => {
    mutations.forEach((mutation) => {
      $(mutation.addedNodes)
        .find(target)
        .each((_, node) => callback(node));
    });
  }).observe(container, { childList: true, subtree: true });
}

export const call = function ({ url, data, form, callback }) {
  let params = {
    type: "POST",
    url: url,
    success: function (results) {
      processResults(callback, results);
    },
    error: function (error) {
      let message = `Error HTTP ${error.status}: ${error.statusText}.`;
      if (error.status == 400) {
        message += " Your session might have expired, try refreshing the page.";
      } else if (error.status == 403) {
        message = "Error 403 - Not Authorized.";
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

export function serializeForm(form, formDefault) {
  const data = JSON.parse(JSON.stringify($(form).serializeArray()));
  let result = {};
  data.forEach((property) => {
    const propertyType = formProperties[formDefault]?.[property.name]?.type;
    if (propertyType && propertyType.includes("object")) {
      if (!(property.name in result)) result[property.name] = [];
      result[property.name].push(property.value);
    } else if (property.value) {
      result[property.name] = property.value;
    }
  });
  return result;
}

const deleteInstance = function (type, id, tableId) {
  call({
    url: `/delete_instance/${type}/${id}`,
    callback: function (name) {
      if (type in subtypes.service) {
        type = "service";
        const path = localStorage.getItem("path");
        if (path && path.includes(id)) {
          localStorage.removeItem("path");
        }
      }
      if (tableId) {
        tableInstances[tableId].table
          .row($(`#${id}`))
          .remove()
          .draw(false);
      }
      notify(`${type.toUpperCase()} '${name}' deleted.`, "success", 5, true);
    },
  });
};

function removeInstance(tableId, instance, relation) {
  call({
    url: "/remove_instance",
    data: { instance, relation },
    callback: function () {
      refreshTable(tableId, false, true);
      notify(
        `${instance.type.toUpperCase()} '${instance.name}' removed from
        ${relation.type.toUpperCase()} '${relation.name}'.`,
        "success",
        5,
        true
      );
    },
  });
}

export function downloadFile(name, content, type) {
  let link = document.createElement("a");
  link.setAttribute(
    "href",
    window.URL.createObjectURL(
      new Blob([content], {
        type: type ? `text/${type}` : "text/plain",
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

export function createTooltips(panel) {
  $(panel || "html")
    .find("[data-tooltip]")
    .each(function () {
      const id = `tooltip-${$(this).attr("data-tooltip").replace(/\s/g, "")}`;
      jsPanel.tooltip.create({
        id: id,
        borderRadius: "10px",
        callback: () => setTimeout(() => $(`#${id}`).fadeOut(1000), 2500),
        content: `<p style="margin-right: 10px; margin-left: 10px;
        margin-bottom: 3px; color: white"><b>${$(this).attr("data-tooltip")}</b></p>`,
        contentSize: "auto",
        connector: true,
        delay: 800,
        header: false,
        opacity: 0.8,
        position: {
          my: "center-bottom",
          at: "center-top",
          of: this,
        },
        target: this,
        theme: "dark filleddark",
      });
    });
}

export function loadTypes(model) {
  const subtypeModel = model == "edge" ? "link" : model;
  $(`#${model}-type-list`).selectpicker({ liveSearch: true });
  for (const [subtype, name] of Object.entries(subtypes[subtypeModel])) {
    if (page == "device_table" && subtype == "network") continue;
    $(`#${model}-type-list`).append(new Option(name, subtype));
  }
  $(`#${model}-type-list`).selectpicker("refresh");
}

function createNotificationBanner() {
  if (!parameters.banner_active) return;
  jsPanel.hint.create(parameters.banner_properties);
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
  tableId,
  url,
  css,
  checkRbac = true,
  ...other
}) {
  const endpoint = url || `/${name}_form`;
  if (
    checkRbac &&
    !user.is_admin &&
    !user.get_requests.includes(endpoint) &&
    rbac.get_requests[endpoint] != "all"
  ) {
    return notify("Error 403 - Not Authorized.", "error", 5);
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
    headerLogo: "/static/img/logo.png",
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
      stop: function () {
        if (tableId) refreshTable(tableId);
      },
    },
    ...other,
  };
  if (content) {
    kwargs.content = content;
  } else {
    kwargs.contentAjax = {
      url: url || `/${name}_form`,
      done: function (_, panel) {
        panel.content.innerHTML = this.responseText;
        preprocessForm(panel, id, type, duplicate);
        configureForm(name, id, panelId);
        if (callback) callback(panel);
      },
    };
  }
  const panel = jsPanel.create(kwargs);
  if (callback && content) callback(content);
  createTooltips(panel);
  const position = { top: `${50 + $(window).scrollTop()}px`, position: "absolute" };
  $(panel).css({ ...position, ...css });
}

export function showConfirmationPanel({
  id,
  title,
  message,
  confirmButton = "Confirm",
  onConfirm,
}) {
  const content = `
  <div class="modal-body" style="max-width:600px">${message}</div>
  <div class="modal-footer">
    <center>
      <button type="button" class="btn btn-danger confirmAction">
        ${confirmButton}
      </button>
    </center>
  </div><br>`;
  openPanel({
    name: "confirmation",
    id: id,
    title: title,
    content: content,
    size: "auto",
    checkRbac: false,
  });
  $(".confirmAction").click(function () {
    onConfirm();
    $(`#confirmation-${id}`).remove();
  });
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
  ...other
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
        done: function (_, panel) {
          panel.content.innerHTML = this.responseText;
          preprocessForm(panel);
          configureForm(name, undefined, `tooltip-${name}`);
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

function showDeletionPanel(instance, tableId) {
  showConfirmationPanel({
    id: `${instance.type}-${instance.id}`,
    title: `Delete ${instance.type} '${instance.name}'`,
    message: "Are you sure you want to permanently remove this item ?",
    confirmButton: "Delete",
    onConfirm: () => deleteInstance(instance.type, instance.id, tableId),
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
      const property = type in subtypes.service ? "scoped_name" : "name";
      if (
        [property, "id"].includes(el.name) ||
        formProperties[type][el.name]?.dont_duplicate
      ) {
        return;
      }
    }
    if (id) $(el).prop("id", `${$(el).attr("id")}-${id}`);
  });
  panel.querySelectorAll(".href-id").forEach((el) => {
    if (id) $(el).prop("href", `${$(el).attr("href")}-${id}`);
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
      const propertyName = helpUrl.split("/").at(-1);
      openPanel({
        name: `help-${propertyName}`,
        title: propertyName.replace("_", " "),
        size: "600px auto",
        url: `/help/${helpUrl}`,
        callback: function (helpPanel) {
          helpPanel.querySelectorAll(".help-snippet").forEach((el) => {
            const editor = CodeMirror.fromTextArea(el, {
              lineNumbers: true,
              readOnly: true,
            });
            editor.setSize("100%", "fit-content");
          });
        },
        checkRbac: false,
      });
    });
    $(el).append(button);
  });
}

export function initCodeMirror(id, mode) {
  const element = document.getElementById(id);
  // eslint-disable-next-line new-cap
  const editor = CodeMirror(element, {
    lineWrapping: true,
    lineNumbers: true,
    readOnly: true,
    theme: "cobalt",
    mode: mode,
    extraKeys: { "Ctrl-F": "findPersistent" },
  });
  $(`#${id}`).data("CodeMirrorInstance", editor);
  editor.setSize("100%", "100%");
  new ResizeObserver(() => {
    editor.refresh();
  }).observe(element);
  return editor;
}

export function initSelect(el, model, parentId, single, constraints) {
  el.select2({
    multiple: !single,
    allowClear: true,
    placeholder: `Select ${single ? `a ${model}` : `${model}s`}`,
    closeOnSelect: single ? true : false,
    dropdownParent: parentId ? $(`#${parentId}`) : $(document.body),
    tags: !single,
    escapeMarkup: (markup) => markup,
    width: "100%",
    tokenSeparators: [","],
    ajax: {
      url: `/multiselect_filtering/${model}`,
      type: "POST",
      delay: 250,
      contentType: "application/json",
      data: function (params) {
        return JSON.stringify({
          term: params.term || "",
          page: params.page || 1,
          constraints: constraints,
          multiple: !single,
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
    } else if (["list", "multiselect"].includes(field.type)) {
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
      if (relationships?.[form]?.[property]?.model) {
        model = relationships[form][property].model;
      } else {
        model = field.model;
      }
      initSelect(el, model, panelId, field.type == "object", field.constraints);
    }
  }
}

function showAddInstancePanel(tableId, model, relation) {
  openPanel({
    name: `add_${model}s`,
    size: "800 300",
    title: `Add ${model}s to ${relation.name}`,
    id: tableId,
    type: model,
    callback: () => {
      $(`#add_${model}s-relation_id-${tableId}`).val(relation.id);
      $(`#add_${model}s-relation_type-${tableId}`).val(relation.type);
      $(`#add_${model}s-property-${tableId}`).val(relation.relation.to);
    },
  });
}

function addInstancesToRelation(type, id) {
  call({
    url: `/add_instances_in_bulk`,
    form: `add_${type}s-form-${id}`,
    callback: (result) => {
      $(`#add_${type}s-${id}`).remove();
      refreshTable(id, false, true);
      notify(
        `${result.number} ${type}s added to
        ${result.target.type} '${result.target.name}'.`,
        "success",
        5,
        true
      );
    },
  });
}

export function showInstancePanel(type, id, mode, tableId, edge) {
  openPanel({
    name: type,
    id: id || tableId,
    footerToolbar: `
      <div style="width: 100%; height: 40px; display: flex;
        align-items: center; justify-content: center;">
        <button
          style="width: 100px"
          id="${type}-action-btn"
          type="button"
          class="btn btn-success btn-id add-id"
          value="eNMS.base.processData"
        >
          Save
        </button>
      </div>`,
    callback: function (panel) {
      const isService = type in subtypes.service;
      const isNode = type in subtypes.node;
      const isLink = type in subtypes.link;
      if (isService) showServicePanel(type, id, mode, tableId);
      if (isNode) showNodePanel(type, id, mode, tableId);
      if (isLink) showLinkPanel(type, id, edge);
      if (type == "credential") showCredentialPanel(id);
      if (type == "folder") showFolderPanel(id);
      if (id) {
        call({
          url: `/get/${type}/${id}`,
          callback: function (instance) {
            const ownersNames = instance.owners
              ? instance.owners.map((user) => user.name)
              : [];
            const allowedUser = user.is_admin || ownersNames.includes(user.name);
            $(`#rbac-properties-${id} *`).prop("disabled", !allowedUser);
            const action = mode ? mode.toUpperCase() : "EDIT";
            panel.setHeaderTitle(`${action} ${type} - ${instance.name}`);
            processInstance(type, instance);
            if (isService) loadScript(`../static/js/services/${type}.js`, id);
          },
        });
      } else if (mode == "bulk-edit") {
        buildBulkEditPanel(panel, type, tableId);
      } else if (mode == "bulk-filter") {
        buildBulkFilterPanel(panel, type, tableId);
      } else {
        panel.setHeaderTitle(`Create a New ${type}`);
        if (page == "workflow_builder" && creationMode == "create_service") {
          $(`#${type}-workflows`).append(new Option(instance.name, instance.name));
          $(`#${type}-workflows`).val(instance.name).trigger("change");
        }
        if (page == "network_builder") updateNetworkPanel(type);
      }
      if (isService && !id) loadScript(`../static/js/services/${type}.js`);
      const property = isService
        ? "scoped_name"
        : type == "folder"
        ? "filename"
        : "name";
      $(`#${type}-${property}`).focus();
    },
    type: type,
    duplicate: mode == "duplicate",
  });
}

function buildBulkEditPanel(panel, type, tableId) {
  const model = type in subtypes.service ? "service" : type;
  for (const [property, value] of Object.entries(formProperties[type])) {
    if (value.type == "object-list") {
      $(`#${type}-${property}-property-div-${tableId}`).width("80%").before(`
          <div style="float:right; width: 19%; margin-top: 2px;">
            <select
              data-width="100%"
              id="${tableId}-${property}-list"
              name="${property}-edit-mode"
            >
              <option value="set">Set</option>
              <option value="append">Append</option>
              <option value="remove">Remove</option>
            </select>
          </div>
        `);
      $(`#${tableId}-${property}-list`).selectpicker();
    }
    if (["name", "scoped_name", "type"].includes(property)) {
      $(`#${type}-${property}-${tableId}`).prop("readonly", true);
    } else {
      $(`label[for='${property}']`).after(`
        <div class="item" style='float:right; margin-left: 15px'>
          <input
            id="bulk-edit-${property}-${tableId}"
            name="bulk-edit-${property}"
            type="checkbox"
          />
        </div>
      `);
    }
  }
  const form = {
    ...serializeForm(`#search-form-${tableId}`, `${model}_filtering`),
    ...tableInstances[tableId].constraints,
    ...tableInstances[tableId].filteringConstraints,
  };
  const rbac = tableId.includes("configuration") ? "configuration" : "read";
  call({
    url: `/filtering/${model}`,
    data: { form: form, bulk: "id", rbac: rbac },
    callback: function (instances) {
      $(`#${type}-id-${tableId}`).val(instances.join("-"));
      $(`#${type}-scoped_name-${tableId},#${type}-name-${tableId}`).val("Bulk Edit");
      const number = instances.length;
      panel.setHeaderTitle(`Edit all ${number} ${model}s in table in bulk`);
      $(`#${type}-action-btn-${tableId}`)
        .attr(
          "onclick",
          `eNMS.table.showBulkEditPanel(
          '${type}', '${model}', '${tableId}', ${number})`
        )
        .text("Bulk Edit");
    },
  });
}

function buildBulkFilterPanel(panel, type, tableId) {
  const model = type in subtypes.service ? "service" : type;
  panel.setHeaderTitle(`Filter all ${model}s in table`);
  $(`#${type}-creator-${tableId}`).prop("readonly", false);
  for (const [property, value] of Object.entries(formProperties[type])) {
    if (value.type == "object-list") {
      $(`#${type}-${property}-property-div-${tableId}`).width("80%").before(`
          <div style="float:right; width: 19%; margin-top: 2px;">
            <select
              data-width="100%"
              id="${tableId}-${property}-list"
              name="${property}_filter"
            >
              <option value="union">Union</option>
              <option value="intersection">Intersection</option>
              <option value="empty">Empty</option>
            </select>
          </div>
        `);
      $(`#${tableId}-${property}-list`).selectpicker();
    } else if (["str", "integer", "list"].includes(value.type)) {
      $(`#${type}-${property}-property-div-${tableId}`).width("80%").before(`
          <div style="float:right; width: 19%; margin-top: 2px;">
            <select
              data-width="100%"
              id="${tableId}-${property}-list"
              name="${property}_filter"
            >
              <option value="inclusion">Inclusion</option>
              <option value="equality">Equality</option>
              <option value="regex">Regular Expression</option>
              <option value="empty">Empty</option>
            </select>
          </div>
        `);
      $(`#${tableId}-${property}-list`).selectpicker();
    }
    $(`label[for='${property}']`).after(`
      <div class="item" style='float:right; margin-left: 15px'>
        <input
          id="bulk-filter-${property}-${tableId}"
          name="bulk-filter-${property}"
          data-property="${property}"
          type="checkbox"
        />
      </div>
    `);
  }
  $(`#${type}-action-btn-${tableId}`)
    .attr(
      "onclick",
      `eNMS.table.refreshTable('${tableId}', false, true)`
    )
    .text("Bulk Filter");
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
  } else if (["list", "multiselect"].includes(propertyType)) {
    try {
      el.selectpicker("deselectAll");
    } catch (e) {
      // ignore
    }
    el.selectpicker("val", value).trigger("change");
    el.selectpicker("render");
  } else if (["object-list", "object"].includes(propertyType)) {
    if (propertyType == "object") value = [value];
    const idProperty = propertyType == "object" ? "id" : "name";
    value.forEach((o) => {
      const uiLink = `
      <button type="button" title="" class="btn btn-link btn-select2"
      onclick="eNMS.base.showInstancePanel('${o.type}', '${o.id}')">
      ${o.ui_name || o.name}</button>`;
      el.append(new Option(uiLink, o[idProperty]));
    });
    el.val(value.map((p) => p[idProperty])).trigger("change");
  } else if (propertyType == "json") {
    el.val(JSON.stringify(value));
    const editor = jsonEditors[instance.id][property];
    if (editor) editor.set(value);
    if (el.attr("class").includes("collapse")) editor.collapseAll();
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

export function processInstance(type, instance) {
  for (const [property, value] of Object.entries(instance)) {
    const el = $(
      instance ? `#${type}-${property}-${instance.id}` : `#${type}-${property}`
    );
    const isList = formProperties?.[type]?.[property]?.type == "field-list";
    if (!el.length && !isList) continue;
    updateProperty(instance, el, property, value, type);
  }
}

function processData(type, id) {
  if (type in subtypes.service || type in subtypes.node || type in subtypes.link) {
    const relation = type in subtypes.service ? "workflow" : "network";
    const property = id ? `#${type}-${relation}s-${id}` : `#${type}-${relation}s`;
    $(property).prop("disabled", false);
  }
  if (type == "folder" && !id) {
    const filename = $("#folder-filename").val();
    $("#folder-path").val(`${folderPath}/${filename}`);
  }
  call({
    url: `/update/${type}`,
    form: id ? `${type}-form-${id}` : `${type}-form`,
    callback: (instance) => {
      if (page.includes("table")) {
        refreshTable(page.split("_")[0]);
      } else if (page.includes("builder")) {
        processBuilderData(instance, id);
      }
      $(id ? `#${type}-${id}` : `#${type}`).remove();
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

(function ($) {
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

export function copyToClipboard({ text, isId, includeText = true }) {
  if (isId) text = $(`#${text}`).val();
  let dummy = document.createElement("textarea");
  document.body.appendChild(dummy);
  dummy.value = text;
  dummy.select();
  document.execCommand("copy");
  document.body.removeChild(dummy);
  notify(`Copied to Clipboard${includeText ? `: ${text}` : "."}`, "success", 5);
}

export function moveHistory(path, direction) {
  if (!direction) {
    historyPosition++;
    history.splice(historyPosition, 9e9, path);
  } else {
    historyPosition += direction == "right" ? 1 : -1;
  }
  if (history.length >= 1 && historyPosition !== 0) {
    $("#left-arrow").removeClass("disabled");
  } else {
    $("#left-arrow").addClass("disabled");
  }
  if (historyPosition < history.length - 1) {
    $("#right-arrow").removeClass("disabled");
  } else {
    $("#right-arrow").addClass("disabled");
  }
}

export function setTriggerMenu(value) {
  triggerMenu = value;
}

(function ($, window) {
  $.fn.contextMenu = function (settings) {
    return this.each(function () {
      $(this).on("contextmenu", function (e) {
        if (e.ctrlKey || !triggerMenu) return;
        const $menu = $(settings.menuSelector)
          .show()
          .css({
            position: "absolute",
            left: getMenuPosition(e.clientX, "width", "scrollLeft"),
            top: getMenuPosition(e.clientY, "height", "scrollTop") + 60,
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
})($, window);

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
    title: "Alerts",
    size: "1200 500",
    callback: () => {
      $("#alerts-table")
        // eslint-disable-next-line new-cap
        .DataTable({
          pagingType: "full_numbers",
          sDom: `<"row view-filter"<"col-sm-12"<"pull-left"l><"pull-right"f>
            <"clearfix">>>t<"row view-pager"<"col-sm-12"<"text-center"ip>>>`,
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
          </span><br />
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

function switchTheme(theme) {
  $(`link[href="/static/css/themes/${currentTheme}.css"]`).remove();
  currentTheme = theme;
  let cssLink = document.createElement("link");
  cssLink.rel = "stylesheet";
  cssLink.type = "text/css";
  cssLink.href = `/static/css/themes/${theme}.css`;
  document.getElementsByTagName("head")[0].appendChild(cssLink);
  call({ url: `/switch_theme/${user.id}/${theme}` });
}

function initSidebar() {
  $("#sidebar-menu")
    .find("a")
    .on("click", function () {
      let $li = $(this).parent();
      if ($li.is(".active")) {
        $li.removeClass("active active-sm");
        $("ul:first", $li).slideUp();
      } else {
        if (!$li.parent().is(".child_menu")) {
          $("#sidebar-menu").find("li").removeClass("active active-sm");
          $("#sidebar-menu").find("li ul").slideUp();
        } else {
          if ($("body").is(".nav-sm")) {
            if (!$li.parent().is(".child_menu")) {
              $("#sidebar-menu").find("li").removeClass("active active-sm");
              $("#sidebar-menu").find("li ul").slideUp();
            }
          }
        }
        $li.addClass("active");
        $("ul:first", $li).slideDown();
      }
    });

  let switchMenu = function () {
    if ($("body").hasClass("nav-sm")) {
      $("#eNMS").css({ "font-size": "17px" });
      $("#eNMS-version").css({ "font-size": "15px" });
      $("#sidebar-menu").find("li.active ul").hide();
      $("#sidebar-menu").find("li.active").addClass("active-sm");
      $("#sidebar-menu").find("li.active").removeClass("active");
    } else {
      $("#eNMS").css({ "font-size": "30px" });
      $("#eNMS-version").css({ "font-size": "20px" });
      $("#sidebar-menu").find("li.active-sm ul").show();
      $("#sidebar-menu").find("li.active-sm").addClass("active");
      $("#sidebar-menu").find("li.active-sm").removeClass("active-sm");
      const url = "a[href='" + currentUrl + "']";
      $("#sidebar-menu").find(url).parent("li").addClass("current-page");
      $("#sidebar-menu")
        .find("a")
        .filter(function () {
          return this.href == currentUrl;
        })
        .parent("li")
        .addClass("current-page")
        .parents("ul")
        .slideDown()
        .parent()
        .addClass("active");
    }
    $(".dataTable").each(function () {
      $(this).dataTable().fnDraw();
    });
  };

  switchMenu();
  $("#menu_toggle").on("click", function () {
    call({ url: `/switch_menu/${user.id}` });
    $("body").toggleClass("nav-md nav-sm");
    $("#server-time").hide();
    switchMenu();
  });
}

$(document).ready(function () {
  $("#eNMS").on("click", function (event) {
    if (!event.altKey || !event.shiftKey || !user.is_admin) return;
    openDebugPanel();
  });
  NProgress.start();
  const alerts = localStorage.getItem("alerts");
  if (!alerts) {
    localStorage.setItem("alerts", "[]");
  } else {
    const alertNumber = JSON.parse(alerts).length;
    $("#alert-number").text(alertNumber > 99 ? "99+" : alertNumber || "");
  }
  $("#theme").selectpicker();
  initSidebar();
  if (page.includes("table")) {
    const type = page.split("_")[0];
    new tables[type]();
  } else if (page.includes("builder")) {
    initBuilder();
  } else if (page.includes("view")) {
    initVisualization();
  } else if (page == "dashboard") {
    initDashboard();
  }
  detectUserInactivity();
  createTooltips();
  createNotificationBanner();
});

$(window).load(function () {
  NProgress.done();
});

configureNamespace("base", [
  addInstancesToRelation,
  call,
  clearAlerts,
  copyToClipboard,
  createAlerts,
  fullScreen,
  loadScript,
  openPanel,
  processData,
  processInstance,
  removeInstance,
  showAddInstancePanel,
  showAllAlerts,
  showDeletionPanel,
  showInstancePanel,
  switchTheme,
]);
