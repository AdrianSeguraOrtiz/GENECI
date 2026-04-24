import { $ } from "../core/dom.js";
import { conditionalRuleMatches, deepEqualJson, readParamsFromHost, renderParamsHost, resolvedDefaultParams, setParamFieldError } from "/static-common/app/params/schema_form.js?v=20260423c";

let getToolByIdFn = null;
let listAvailableToolsFn = null;
let listProvidedExtraKeysFn = null;
let defaultGroupModeForToolFn = null;
let openParamsModalFn = null;
let onRunsChangedFn = null;

export function initRunCards({
  getToolById,
  listAvailableTools,
  listProvidedExtraKeys,
  defaultGroupModeForTool,
  openParamsModal,
  onRunsChanged,
}) {
  getToolByIdFn = getToolById;
  listAvailableToolsFn = listAvailableTools;
  listProvidedExtraKeysFn = listProvidedExtraKeys;
  defaultGroupModeForToolFn = defaultGroupModeForTool;
  openParamsModalFn = openParamsModal;
  onRunsChangedFn = onRunsChanged;
}

function notifyRunsChanged() {
  if (typeof onRunsChangedFn === "function") {
    onRunsChangedFn();
  }
}

export function buildRunId(toolId) {
  const cards = Array.from(document.querySelectorAll(".run-card"));
  const prefixes = cards
    .map((card) => card.querySelector(".run-id"))
    .map((input) => String(input?.value || "").trim())
    .filter(Boolean);
  let suffix = 1;
  while (prefixes.includes(`${toolId}__${String(suffix).padStart(2, "0")}`)) {
    suffix += 1;
  }
  return `${toolId}__${String(suffix).padStart(2, "0")}`;
}

export function updateRunsEmptyState() {
  const hasRuns = document.querySelectorAll(".run-card").length > 0;
  $("runs-empty").style.display = hasRuns ? "none" : "block";
}

export function readParamsFromCard(card) {
  const tool = getToolByIdFn?.(String(card.querySelector(".tool-id")?.value || "").trim());
  if (!tool) {
    throw new Error("Unknown tool");
  }
  return readParamsFromHost(tool, card.querySelector(".run-params-form"));
}

function updateRunParamsSummary(card, tool, params = null) {
  const summaryEl = card.querySelector(".run-params-summary");
  if (!summaryEl) {
    return;
  }
  const currentParams = params || readParamsFromCard(card);
  const defaultParams = resolvedDefaultParams(tool);
  summaryEl.textContent = deepEqualJson(currentParams, defaultParams)
    ? "Default parameters"
    : "Custom parameters";
}

export function renderRunParamsForm(card, tool, initialParams = null) {
  const host = card.querySelector(".run-params-form");
  renderParamsHost(host, tool, initialParams, () => {
    refreshRunCardsValidation();
    notifyRunsChanged();
  });
  updateRunParamsSummary(card, tool, readParamsFromHost(tool, host));
}

function validateRunCard(card) {
  const toolId = String(card.querySelector(".tool-id")?.value || "").trim();
  const tool = getToolByIdFn?.(toolId);
  const validationEl = card.querySelector(".run-validation");
  const messages = [];
  const runId = String(card.querySelector(".run-id")?.value || "").trim();

  card.querySelectorAll(":scope .param-field").forEach((field) => setParamFieldError(field, ""));

  if (!runId) {
    messages.push("Run ID is required.");
  }

  let params = {};
  try {
    params = readParamsFromCard(card);
  } catch (err) {
    const message = String(err?.message || "Invalid parameter value").trim();
    messages.push(message);
    const [fieldPath] = message.split(":");
    const fieldName = String(fieldPath || "").split(".")[0];
    if (fieldName) {
      const field = card.querySelector(`.run-params-form > .param-field[data-param-key="${CSS.escape(fieldName)}"]`);
      if (field) {
        setParamFieldError(field, message);
      }
    }
  }

  if (tool) {
    const providedExtras = listProvidedExtraKeysFn ? listProvidedExtraKeysFn() : new Set();
    const missingRequired = (Array.isArray(tool.required_extras) ? tool.required_extras : [])
      .filter((key) => !providedExtras.has(String(key)));
    for (const key of missingRequired) {
      messages.push(`Missing input: ${key}`);
    }

    const conditionalRules = Array.isArray(tool.conditional_required_extras)
      ? tool.conditional_required_extras
      : [];
    for (const rule of conditionalRules) {
      const inputKey = String(rule?.input || "").trim();
      const message = String(rule?.message || "").trim();
      if (!inputKey || !message) {
        continue;
      }
      if (providedExtras.has(inputKey)) {
        continue;
      }
      if (conditionalRuleMatches(params, rule)) {
        messages.push(message);
      }
    }

    const groupMode = String(card.querySelector(".execution-group-mode")?.value || "").trim();
    if (String(tool.execution_scope || "").trim() === "group" && groupMode !== "per_group") {
      messages.push("This tool executes per group natively.");
    }
    if (groupMode === "per_group" && !providedExtras.has("groups")) {
      messages.push("Per-group execution requires groups.tsv.");
    }
  }

  const uniqueMessages = [...new Set(messages.filter(Boolean))];
  card.classList.toggle("invalid", uniqueMessages.length > 0);
  if (validationEl) {
    validationEl.classList.remove("ok", "err");
    if (!uniqueMessages.length) {
      validationEl.classList.add("ok");
      validationEl.textContent = "Run configuration looks valid.";
    } else {
      validationEl.classList.add("err");
      validationEl.innerHTML = "";
      for (const message of uniqueMessages) {
        const line = document.createElement("div");
        line.textContent = message;
        validationEl.appendChild(line);
      }
    }
  }
  return uniqueMessages;
}

export function refreshRunCardsValidation() {
  const cards = Array.from(document.querySelectorAll(".run-card"));
  let hasInvalid = false;
  for (const card of cards) {
    if (validateRunCard(card).length) {
      hasInvalid = true;
    }
  }
  return !hasInvalid;
}

export function addRunCard(initial = {}) {
  const template = $("run-template");
  const node = template.content.firstElementChild.cloneNode(true);

  const runIdInput = node.querySelector(".run-id");
  const toolInput = node.querySelector(".tool-id");
  const toolNameEl = node.querySelector(".run-tool-name");
  const executionModeInput = node.querySelector(".execution-group-mode");
  const openParamsBtn = node.querySelector(".open-params");
  const resetParamsBtn = node.querySelector(".reset-params");
  const removeBtn = node.querySelector(".remove-run");

  const availableTools = listAvailableToolsFn ? listAvailableToolsFn() : [];
  if (!availableTools.length) {
    throw new Error("No eligible tools available. Analyze inputs first.");
  }

  const initialToolId = initial.tool_id || availableTools[0]?.tool_id || "";
  const tool = getToolByIdFn?.(initialToolId);
  if (!tool) {
    throw new Error(`Unknown tool_id '${initialToolId}'`);
  }
  toolInput.value = tool.tool_id;
  toolNameEl.textContent = tool.name;
  const executionScope = String(tool.execution_scope || "").trim();
  const initialGroupMode = String(initial?.execution?.group_mode || "").trim();
  const selectedGroupMode = initialGroupMode || defaultGroupModeForToolFn?.(tool) || "global";

  executionModeInput.innerHTML = "";
  const modeOptions =
    executionScope === "group"
      ? [{ value: "per_group", label: "Per group" }]
      : [
          { value: "global", label: "Global" },
          { value: "per_group", label: "Per group" },
        ];
  for (const optionMeta of modeOptions) {
    const option = document.createElement("option");
    option.value = optionMeta.value;
    option.textContent = optionMeta.label;
    executionModeInput.appendChild(option);
  }
  executionModeInput.value = modeOptions.some((item) => item.value === selectedGroupMode)
    ? selectedGroupMode
    : modeOptions[0].value;
  executionModeInput.disabled = executionScope === "group";
  executionModeInput.title =
    executionScope === "group"
      ? "This tool executes by group natively."
      : "Choose whether to run the tool once globally or once per group.";

  runIdInput.value = initial.run_id || buildRunId(tool.tool_id);
  renderRunParamsForm(node, tool, initial.params || null);

  runIdInput.addEventListener("input", () => {
    refreshRunCardsValidation();
    notifyRunsChanged();
  });
  executionModeInput.addEventListener("change", () => {
    refreshRunCardsValidation();
    notifyRunsChanged();
  });
  openParamsBtn.addEventListener("click", () => {
    if (typeof openParamsModalFn === "function") {
      openParamsModalFn(node);
    }
  });
  resetParamsBtn.addEventListener("click", () => {
    renderRunParamsForm(node, tool, resolvedDefaultParams(tool));
    refreshRunCardsValidation();
    notifyRunsChanged();
  });

  removeBtn.addEventListener("click", () => {
    node.remove();
    updateRunsEmptyState();
    refreshRunCardsValidation();
    notifyRunsChanged();
  });

  $("runs-container").appendChild(node);
  updateRunsEmptyState();
  refreshRunCardsValidation();
  notifyRunsChanged();
}

export function collectRuns() {
  const cards = Array.from(document.querySelectorAll(".run-card"));
  if (!cards.length) {
    throw new Error("At least one run is required.");
  }
  if (!refreshRunCardsValidation()) {
    const firstInvalid = cards.find((card) => card.classList.contains("invalid"));
    const firstMessage =
      firstInvalid?.querySelector(".run-validation > div")?.textContent ||
      firstInvalid?.querySelector(".run-validation")?.textContent ||
      "Fix invalid run configuration before planning.";
    throw new Error(String(firstMessage).trim());
  }

  const seen = new Set();
  const runs = [];
  cards.forEach((card, idx) => {
    const runId = card.querySelector(".run-id").value.trim();
    const toolId = card.querySelector(".tool-id").value;

    if (!runId) {
      throw new Error(`Run ${idx + 1}: run_id is required.`);
    }
    if (seen.has(runId)) {
      throw new Error(`Duplicate run_id: ${runId}`);
    }
    seen.add(runId);

    let params = {};
    try {
      params = readParamsFromCard(card);
    } catch (err) {
      throw new Error(`Run ${idx + 1} params: ${String(err?.message || "invalid value")}`);
    }

    runs.push({
      run_id: runId,
      tool_id: toolId,
      params,
      execution: {
        group_mode: card.querySelector(".execution-group-mode").value,
      },
    });
  });
  return runs;
}
