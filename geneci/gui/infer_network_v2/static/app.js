const state = {
  bootstrap: null,
  jobId: null,
  stage: "draft",
  preflightReport: null,
  lastPlan: null,
  lastNetworkPreview: null,
  runtimeProgress: null,
  pollTimer: null,
  loadedPlanKey: null,
  loadedNetworkKey: null,
  loadedFilesKey: null,
  selectedFilePath: null,
  filesEntries: [],
  filesMode: "light",
  collapsedDirs: new Set(),
  eligibleToolIds: null,
  activeStep: 1,
  notifiedFailures: new Set(),
  notifiedJobError: "",
};
const NETWORK_PREVIEW_MAX_EDGES = 300;

function $(id) {
  return document.getElementById(id);
}

function pushToast({ title, message, kind = "error", ttlMs = 7000 }) {
  const host = $("toast-container");
  if (!host) {
    return;
  }
  const toast = document.createElement("article");
  toast.className = `toast ${kind}`;

  const textWrap = document.createElement("div");
  const titleNode = document.createElement("p");
  titleNode.className = "toast-title";
  titleNode.textContent = String(title || "Notice");
  const bodyNode = document.createElement("p");
  bodyNode.className = "toast-body";
  bodyNode.textContent = String(message || "").trim() || "-";
  textWrap.appendChild(titleNode);
  textWrap.appendChild(bodyNode);

  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "toast-close";
  closeBtn.textContent = "×";
  closeBtn.setAttribute("aria-label", "Close notification");
  closeBtn.addEventListener("click", () => toast.remove());

  toast.appendChild(textWrap);
  toast.appendChild(closeBtn);
  host.appendChild(toast);

  if (ttlMs > 0) {
    window.setTimeout(() => {
      toast.remove();
    }, ttlMs);
  }
}

function currentBundleMode() {
  const mode = $("bundle-mode")?.value || "light";
  return mode === "full" ? "full" : "light";
}

function formatBytes(bytes) {
  if (bytes === null || bytes === undefined || Number.isNaN(Number(bytes))) {
    return "-";
  }
  const value = Number(bytes);
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  if (value < 1024 * 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function getExpressionHelp() {
  const help = state.bootstrap?.dataset_input_help?.expression_matrix || {};
  return {
    description: String(help.description || "").trim(),
    example: String(help.example || "").trim(),
    file_kind: String(help.file_kind || "tsv"),
    delimiter: String(help.delimiter || "\t"),
    header: Boolean(help.header ?? true),
    min_rows: Number.isFinite(Number(help.min_rows)) ? Number(help.min_rows) : 1,
    min_columns: Number.isFinite(Number(help.min_columns)) ? Number(help.min_columns) : 2,
    required_columns: Array.isArray(help.required_columns) ? help.required_columns : [],
    column_types: help.column_types && typeof help.column_types === "object" ? help.column_types : {},
    first_column_role: String(help.first_column_role || "none"),
    first_column_disallowed_names: Array.isArray(help.first_column_disallowed_names)
      ? help.first_column_disallowed_names
      : [],
    unique_first_column: Boolean(help.unique_first_column ?? false),
    data_columns_type: String(help.data_columns_type || "any"),
    data_numeric_min_fraction: Number.isFinite(Number(help.data_numeric_min_fraction))
      ? Number(help.data_numeric_min_fraction)
      : 1.0,
  };
}

function getExtraMeta(key) {
  const list = Array.isArray(state.bootstrap?.extra_inputs) ? state.bootstrap.extra_inputs : [];
  return list.find((item) => item.key === key) || null;
}

function buildInfoTooltip({ title, description, example }) {
  return {
    title: String(title || "").trim(),
    description: String(description || "").trim(),
    example: String(example || "").trim(),
  };
}

function normalizeHelpText(value) {
  const raw = String(value || "");
  if (!raw.includes("\\n") && !raw.includes("\\t") && !raw.includes("\\r")) {
    return raw;
  }
  return raw
    .replace(/\\r\\n/g, "\n")
    .replace(/\\n/g, "\n")
    .replace(/\\t/g, "\t")
    .replace(/\\r/g, "\n");
}

function normalizeUrlOrDoi(value) {
  const raw = String(value || "").trim();
  if (!raw) {
    return null;
  }
  if (/^https?:\/\//i.test(raw)) {
    return raw;
  }
  if (/^doi\.org\//i.test(raw)) {
    return `https://${raw}`;
  }
  if (/^10\.\S+/i.test(raw)) {
    return `https://doi.org/${raw}`;
  }
  return null;
}

function appendLinkifiedText(parent, text) {
  const raw = String(text || "");
  const tokenPattern = /(https?:\/\/[^\s|)]+|doi\.org\/[^\s|)]+|10\.\S+)/gi;
  let lastIndex = 0;
  let match = tokenPattern.exec(raw);
  while (match) {
    const token = match[0];
    if (match.index > lastIndex) {
      parent.appendChild(document.createTextNode(raw.slice(lastIndex, match.index)));
    }
    const href = normalizeUrlOrDoi(token);
    if (href) {
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = token;
      parent.appendChild(anchor);
    } else {
      parent.appendChild(document.createTextNode(token));
    }
    lastIndex = match.index + token.length;
    match = tokenPattern.exec(raw);
  }
  if (lastIndex < raw.length) {
    parent.appendChild(document.createTextNode(raw.slice(lastIndex)));
  }
}

function renderInfoFields(content, fields) {
  const list = document.createElement("dl");
  list.className = "info-kv-list";
  for (const field of fields) {
    if (!field || typeof field !== "object") {
      continue;
    }
    const label = String(field.label || "").trim();
    if (!label) {
      continue;
    }
    const term = document.createElement("dt");
    term.textContent = label;
    const valueNode = document.createElement("dd");

    const links = Array.isArray(field.links) ? field.links.filter((x) => x && typeof x === "object") : [];
    if (links.length) {
      const ul = document.createElement("ul");
      ul.className = "info-link-list";
      for (const item of links) {
        const rawUrl = String(item.url || "").trim();
        const href = normalizeUrlOrDoi(rawUrl);
        const li = document.createElement("li");
        if (href) {
          const anchor = document.createElement("a");
          anchor.href = href;
          anchor.target = "_blank";
          anchor.rel = "noopener noreferrer";
          anchor.textContent = String(item.label || rawUrl || href).trim() || href;
          li.appendChild(anchor);
        } else {
          li.textContent = String(item.label || rawUrl || "-").trim() || "-";
        }
        ul.appendChild(li);
      }
      valueNode.appendChild(ul);
    } else if (field.link && typeof field.link === "object") {
      const rawUrl = String(field.link.url || "").trim();
      const href = normalizeUrlOrDoi(rawUrl);
      if (href) {
        const anchor = document.createElement("a");
        anchor.href = href;
        anchor.target = "_blank";
        anchor.rel = "noopener noreferrer";
        anchor.textContent = String(field.link.label || rawUrl || href).trim() || href;
        valueNode.appendChild(anchor);
      } else {
        appendLinkifiedText(valueNode, String(field.value || "-"));
      }
    } else {
      appendLinkifiedText(valueNode, String(field.value ?? "-"));
    }

    list.appendChild(term);
    list.appendChild(valueNode);
  }
  content.appendChild(list);
}

function showInfoTooltip(payload) {
  if (!payload || typeof payload !== "object") {
    return;
  }
  const popover = $("info-popover");
  const content = $("info-popover-content");
  if (!popover || !content) {
    return;
  }

  const title = normalizeHelpText(String(payload.title || "")).trim();
  const description = normalizeHelpText(String(payload.description || "")).trim();
  const example = normalizeHelpText(String(payload.example || "")).trim();
  const fields = Array.isArray(payload.fields) ? payload.fields : [];
  if (!title && !description && !example && !fields.length) {
    return;
  }

  content.innerHTML = "";
  if (title) {
    const h4 = document.createElement("h4");
    h4.textContent = title;
    content.appendChild(h4);
  }
  if (description) {
    if (description.includes("\n")) {
      const block = document.createElement("div");
      block.className = "info-multiline";
      const lines = description.split("\n");
      for (const line of lines) {
        const p = document.createElement("p");
        appendLinkifiedText(p, line);
        block.appendChild(p);
      }
      content.appendChild(block);
    } else {
      const p = document.createElement("p");
      appendLinkifiedText(p, description);
      content.appendChild(p);
    }
  }
  if (fields.length) {
    renderInfoFields(content, fields);
  }
  if (example) {
    const label = document.createElement("p");
    label.textContent = "Example";
    content.appendChild(label);
    const pre = document.createElement("pre");
    pre.textContent = example;
    content.appendChild(pre);
  }
  popover.classList.remove("hidden");
}

function hideInfoTooltip() {
  const popover = $("info-popover");
  if (!popover) {
    return;
  }
  popover.classList.add("hidden");
}

function readHelpPayload(button) {
  if (!button) {
    return null;
  }
  const raw = String(button.dataset.help || "").trim();
  if (!raw) {
    return null;
  }
  try {
    const payload = JSON.parse(raw);
    return payload && typeof payload === "object" ? payload : null;
  } catch (_err) {
    return null;
  }
}

function setActiveStep(stepNumber, options = {}) {
  const { scroll = true } = options;
  const step = Number(stepNumber);
  if (!Number.isFinite(step) || step < 1 || step > 3) {
    return;
  }
  state.activeStep = step;
  for (const item of document.querySelectorAll(".workflow-step")) {
    const value = Number(item.dataset.step || "0");
    item.classList.toggle("is-active", value === step);
  }
  if (scroll) {
    const panel = $(`step-${step}`);
    if (panel && typeof panel.scrollIntoView === "function") {
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.requestAnimationFrame(() => {
        panel.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
      });
    }
  }
}

function setStepState(stepNumber, value) {
  const badge = $(`step-${stepNumber}-state`);
  if (!badge) {
    return;
  }
  badge.classList.remove("ready", "blocked", "running");
  const normalized = String(value || "blocked");
  if (normalized === "ready") {
    badge.classList.add("ready");
  } else if (normalized === "running") {
    badge.classList.add("running");
  } else {
    badge.classList.add("blocked");
  }
  badge.textContent = normalized;
}

function toolById(toolId) {
  const tools = Array.isArray(state.bootstrap?.tools) ? state.bootstrap.tools : [];
  return tools.find((item) => item.tool_id === toolId) || null;
}

function setStatusBadge(el, kind, text) {
  if (!el) {
    return;
  }
  el.classList.remove("ok", "err");
  if (kind === "ok") {
    el.classList.add("ok");
  } else if (kind === "err") {
    el.classList.add("err");
  }
  el.textContent = text;
}

function _tabularValidationMeta(meta = {}, defaults = {}) {
  const merged = { ...defaults, ...(meta && typeof meta === "object" ? meta : {}) };
  return {
    delimiter: String(merged.delimiter || "\t"),
    hasHeader: Boolean(merged.header ?? true),
    minRows: Number.isFinite(Number(merged.min_rows)) ? Number(merged.min_rows) : 1,
    minColumns: Number.isFinite(Number(merged.min_columns)) ? Number(merged.min_columns) : 1,
    requiredColumns: Array.isArray(merged.required_columns) ? merged.required_columns : [],
    columnTypes: merged.column_types && typeof merged.column_types === "object" ? merged.column_types : {},
    firstColumnRole: String(merged.first_column_role || "none"),
    disallowedFirstHeader: new Set(
      (Array.isArray(merged.first_column_disallowed_names) ? merged.first_column_disallowed_names : [])
        .map((x) => String(x || "").trim().toLowerCase())
        .filter(Boolean)
    ),
    uniqueFirstColumn: Boolean(merged.unique_first_column ?? false),
    dataColumnsType: String(merged.data_columns_type || "any"),
    dataNumericMinFraction: Number.isFinite(Number(merged.data_numeric_min_fraction))
      ? Math.max(0, Math.min(1, Number(merged.data_numeric_min_fraction)))
      : 1.0,
  };
}

function _validateTabularContent(
  raw,
  spec,
  {
    invalidFirstHeaderMessage = (header) => `first column header '${header}' is not valid for this input`,
    emptyFirstValueMessage = (line) => `empty first-column identifier at line ${line}`,
    duplicatedFirstValueMessage = (value, line) =>
      `duplicated first-column identifier '${value}' at line ${line}`,
  } = {}
) {
  const lines = raw.split(/\r?\n/).filter((line) => line.length > 0);
  if (!lines.length) {
    throw new Error("empty file");
  }

  const split = (line) => line.split(spec.delimiter);
  const header = spec.hasHeader ? split(lines[0]) : [];
  if (spec.hasHeader && header.length < 1) {
    throw new Error("invalid header");
  }
  const expectedCols = spec.hasHeader ? header.length : split(lines[0]).length;
  if (expectedCols < spec.minColumns) {
    throw new Error(`expected at least ${spec.minColumns} columns, got ${expectedCols}`);
  }
  if (spec.hasHeader) {
    const headerSet = new Set(header.map((x) => String(x || "").trim()));
    const missing = spec.requiredColumns.filter((col) => !headerSet.has(String(col)));
    if (missing.length) {
      throw new Error(`missing required column(s): ${missing.join(", ")}`);
    }
    if (spec.firstColumnRole === "gene_id") {
      const firstHeader = String(header[0] || "").trim().toLowerCase();
      if (!firstHeader) {
        throw new Error("first column header cannot be empty");
      }
      if (spec.disallowedFirstHeader.has(firstHeader)) {
        throw new Error(invalidFirstHeaderMessage(header[0]));
      }
    }
  } else if (spec.requiredColumns.length) {
    throw new Error("missing required column(s): header is required");
  }

  const firstSeen = new Set();
  let dataCellsTotal = 0;
  let dataCellsNumeric = 0;
  let rows = 0;
  const start = spec.hasHeader ? 1 : 0;
  for (let idx = start; idx < lines.length; idx += 1) {
    const cols = split(lines[idx]);
    if (cols.length !== expectedCols) {
      throw new Error(`inconsistent number of columns at line ${idx + 1}`);
    }
    if (spec.firstColumnRole === "gene_id") {
      const firstValue = String(cols[0] || "").trim();
      if (!firstValue) {
        throw new Error(emptyFirstValueMessage(idx + 1));
      }
      if (spec.uniqueFirstColumn && firstSeen.has(firstValue)) {
        throw new Error(duplicatedFirstValueMessage(firstValue, idx + 1));
      }
      firstSeen.add(firstValue);
    }
    if (spec.dataColumnsType === "float" && cols.length > 1) {
      for (const valueRaw of cols.slice(1)) {
        const value = String(valueRaw || "").trim();
        dataCellsTotal += 1;
        if (value && !Number.isNaN(Number(value))) {
          dataCellsNumeric += 1;
        }
      }
    }
    if (spec.hasHeader) {
      for (const [colName, typeName] of Object.entries(spec.columnTypes)) {
        const colIdx = header.findIndex((x) => String(x || "").trim() === colName);
        if (colIdx < 0) {
          continue;
        }
        const cell = String(cols[colIdx] || "").trim();
        if (!cell) {
          continue;
        }
        if (typeName === "int" && !/^-?\d+$/.test(cell)) {
          throw new Error(`column '${colName}' must be int (line ${idx + 1})`);
        }
        if (typeName === "float" && Number.isNaN(Number(cell))) {
          throw new Error(`column '${colName}' must be float (line ${idx + 1})`);
        }
        if (typeName === "bool" && !["true", "false", "1", "0"].includes(cell.toLowerCase())) {
          throw new Error(`column '${colName}' must be bool (line ${idx + 1})`);
        }
      }
    }
    rows += 1;
  }
  if (rows < spec.minRows) {
    throw new Error(`expected at least ${spec.minRows} row(s), got ${rows}`);
  }
  if (spec.dataColumnsType === "float" && dataCellsTotal > 0) {
    const ratio = dataCellsNumeric / dataCellsTotal;
    if (ratio < spec.dataNumericMinFraction) {
      throw new Error(
        `only ${(ratio * 100).toFixed(1)}% numeric values in data columns (required >= ${(spec.dataNumericMinFraction * 100).toFixed(1)}%)`
      );
    }
  }
  return { rows, columns: expectedCols };
}

async function validateExpressionFile(file) {
  const raw = await file.text();
  const spec = _tabularValidationMeta(getExpressionHelp(), { min_rows: 1, min_columns: 2 });
  const inspected = _validateTabularContent(raw, spec, {
    invalidFirstHeaderMessage: (header) =>
      `first column header '${header}' is not valid for expression genes`,
    emptyFirstValueMessage: (line) => `empty gene identifier at line ${line}`,
    duplicatedFirstValueMessage: (value, line) => `duplicated gene identifier '${value}' at line ${line}`,
  });
  if (inspected.rows < 1) {
    throw new Error("no gene rows found");
  }
  return { genes: inspected.rows, columns: inspected.columns - 1 };
}

async function validateOptionalFile(file, key) {
  const ext = file.name.includes(".") ? file.name.split(".").pop().toLowerCase() : "";
  const meta = getExtraMeta(key);
  const defaultName = String(meta?.default_filename || "");
  const expectedExt = defaultName.includes(".") ? defaultName.split(".").pop().toLowerCase() : "";
  if (expectedExt && ext && ext !== expectedExt) {
    throw new Error(`expected .${expectedExt} file, got .${ext}`);
  }

  const raw = await file.text();
  const lines = raw.split(/\r?\n/).filter((line) => line.length > 0);
  if (!lines.length) {
    throw new Error("empty file");
  }

  const fileKind = String(meta?.file_kind || "").trim() || "tsv";
  const minRows = Number.isFinite(Number(meta?.min_rows)) ? Number(meta?.min_rows) : 0;
  if (fileKind === "txt_list") {
    if (lines.length < minRows) {
      throw new Error(`expected at least ${minRows} non-empty line(s), got ${lines.length}`);
    }
    return { rows: lines.length, columns: 1 };
  }

  const spec = _tabularValidationMeta(meta, { min_rows: 0, min_columns: 1 });
  const inspected = _validateTabularContent(raw, spec, {
    invalidFirstHeaderMessage: (header) =>
      `first column header '${header}' is not valid for this input`,
    emptyFirstValueMessage: (line) => `empty first-column identifier at line ${line}`,
    duplicatedFirstValueMessage: (value, line) =>
      `duplicated first-column identifier '${value}' at line ${line}`,
  });
  return { rows: inspected.rows, columns: inspected.columns };
}

function prettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function parseJsonOrThrow(raw, label) {
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      throw new Error("must be a JSON object");
    }
    return parsed;
  } catch (err) {
    throw new Error(`${label}: invalid JSON (${err.message})`);
  }
}

function buildRunId(toolId) {
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

function updateRunsEmptyState() {
  const hasRuns = document.querySelectorAll(".run-card").length > 0;
  $("runs-empty").style.display = hasRuns ? "none" : "block";
}

function listAvailableTools() {
  const tools = Array.isArray(state.bootstrap?.tools) ? state.bootstrap.tools : [];
  if (!Array.isArray(state.eligibleToolIds) || !state.eligibleToolIds.length) {
    return [];
  }
  const allowed = new Set(state.eligibleToolIds);
  return tools.filter((tool) => allowed.has(tool.tool_id));
}

function addRunCard(initial = {}) {
  const template = $("run-template");
  const node = template.content.firstElementChild.cloneNode(true);

  const runIdInput = node.querySelector(".run-id");
  const toolInput = node.querySelector(".tool-id");
  const toolNameEl = node.querySelector(".run-tool-name");
  const paramsTextarea = node.querySelector(".params-json");
  const removeBtn = node.querySelector(".remove-run");

  const availableTools = listAvailableTools();
  if (!availableTools.length) {
    throw new Error("No eligible tools available. Analyze inputs first.");
  }

  const initialToolId = initial.tool_id || availableTools[0]?.tool_id || "";
  const tool = toolById(initialToolId);
  if (!tool) {
    throw new Error(`Unknown tool_id '${initialToolId}'`);
  }
  toolInput.value = tool.tool_id;
  toolNameEl.textContent = tool.name;

  if (initial.run_id) {
    runIdInput.value = initial.run_id;
  } else {
    runIdInput.value = buildRunId(tool.tool_id);
  }

  if (initial.params) {
    paramsTextarea.value = prettyJson(initial.params);
  } else {
    paramsTextarea.value = prettyJson(tool.default_params);
  }

  removeBtn.addEventListener("click", () => {
    node.remove();
    updateRunsEmptyState();
  });

  $("runs-container").appendChild(node);
  updateRunsEmptyState();
}

function getExtraRows() {
  return Array.from(document.querySelectorAll(".extra-row"));
}

function updateExtrasEmptyState() {
  const hasExtras = getExtraRows().length > 0;
  $("extras-empty").style.display = hasExtras ? "none" : "block";
}

function listExtraKeys() {
  return state.bootstrap.extra_inputs.map((item) => item.key);
}

function syncExpressionHelpTooltip() {
  const infoBtn = $("expression-info-btn");
  if (!infoBtn) {
    return;
  }
  const help = getExpressionHelp();
  const payload = buildInfoTooltip({
    title: "Expression Matrix (TSV)",
    description: help.description || "Tab-separated matrix: first column gene id, rest numeric expression.",
    example: help.example,
  });
  infoBtn.dataset.help = JSON.stringify(payload);
  infoBtn.title = payload.description || payload.title || "Input format info";
}

function syncExpressionFileLabel() {
  const input = $("expression-file");
  const label = $("expression-file-name");
  if (!input || !label) {
    return;
  }
  const file = input.files && input.files[0] ? input.files[0] : null;
  label.textContent = file ? `${file.name} (${formatBytes(file.size)})` : "No file selected";
}

async function handleExpressionSelected(file) {
  const statusEl = $("expression-file-status");
  if (!file) {
    setStatusBadge(statusEl, "", "Pending validation");
    syncExpressionFileLabel();
    return;
  }
  syncExpressionFileLabel();
  try {
    const inspected = await validateExpressionFile(file);
    setStatusBadge(
      statusEl,
      "ok",
      `Valid: ${inspected.genes} gene rows x ${inspected.columns} columns`,
    );
  } catch (err) {
    setStatusBadge(statusEl, "err", `Invalid expression matrix: ${err.message}`);
  }
}

function setInputFile(input, file) {
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
}

function initExpressionDropzone() {
  const dropzone = $("expression-dropzone");
  const input = $("expression-file");
  if (!dropzone || !input) {
    return;
  }

  dropzone.addEventListener("click", () => input.click());
  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("dragover");
  });
  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });
  dropzone.addEventListener("drop", async (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragover");
    const files = event.dataTransfer?.files;
    if (!files || !files.length) {
      return;
    }
    const file = files[0];
    setInputFile(input, file);
    await handleExpressionSelected(file);
  });
  input.addEventListener("change", async () => {
    const file = input.files && input.files[0] ? input.files[0] : null;
    await handleExpressionSelected(file);
  });
}

function syncExtraRowMeta(row) {
  const select = row.querySelector(".extra-key");
  const infoBtn = row.querySelector(".extra-info-btn");
  const fileInput = row.querySelector(".extra-file");
  const fileName = row.querySelector(".extra-file-name");
  const statusEl = row.querySelector(".extra-file-status");
  const key = select.value;
  const meta = getExtraMeta(key);
  const description = String(meta?.description || "").trim();
  const example = String(meta?.example || "").trim();
  const payload = buildInfoTooltip({
    title: key,
    description: description || "Optional input file.",
    example,
  });
  infoBtn.dataset.help = JSON.stringify(payload);
  infoBtn.title = payload.description || payload.title || "Input format info";
  const file = fileInput.files && fileInput.files[0] ? fileInput.files[0] : null;
  fileName.textContent = file ? `${file.name} (${formatBytes(file.size)})` : "No file selected";
  if (!file) {
    setStatusBadge(statusEl, "", "Optional input not provided");
  }
}

async function validateExtraRowFile(row) {
  const select = row.querySelector(".extra-key");
  const fileInput = row.querySelector(".extra-file");
  const statusEl = row.querySelector(".extra-file-status");
  const file = fileInput.files && fileInput.files[0] ? fileInput.files[0] : null;
  const key = select.value;
  if (!file) {
    setStatusBadge(statusEl, "", "Optional input not provided");
    return;
  }
  try {
    const inspected = await validateOptionalFile(file, key);
    const detail =
      inspected.columns !== undefined
        ? `rows=${inspected.rows}, cols=${inspected.columns}`
        : `rows=${inspected.rows}`;
    setStatusBadge(statusEl, "ok", `Looks valid (${detail})`);
  } catch (err) {
    setStatusBadge(statusEl, "err", `Invalid file: ${err.message}`);
  }
}

function refreshExtraSelectOptions() {
  const allKeys = listExtraKeys();
  const rows = getExtraRows();
  for (const row of rows) {
    const select = row.querySelector(".extra-key");
    const current = select.value;
    const usedByOthers = new Set(
      rows
        .filter((candidate) => candidate !== row)
        .map((candidate) => candidate.querySelector(".extra-key").value)
        .filter(Boolean)
    );
    const allowed = allKeys.filter((key) => key === current || !usedByOthers.has(key));
    select.innerHTML = "";
    for (const key of allowed) {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = key;
      select.appendChild(option);
    }
    if (allowed.includes(current)) {
      select.value = current;
    } else if (allowed.length > 0) {
      select.value = allowed[0];
    }
    syncExtraRowMeta(row);
  }
}

function addOptionalExtraRow(preferredKey = null) {
  const allKeys = listExtraKeys();
  const used = new Set(
    getExtraRows()
      .map((row) => row.querySelector(".extra-key").value)
      .filter(Boolean)
  );
  const available = allKeys.filter((key) => !used.has(key));
  if (!available.length) {
    pushToast({
      title: "Optional inputs",
      message: "All optional inputs are already added.",
      kind: "warning",
      ttlMs: 4500,
    });
    return;
  }

  const template = $("extra-template");
  const node = template.content.firstElementChild.cloneNode(true);
  const select = node.querySelector(".extra-key");
  const removeBtn = node.querySelector(".remove-extra");

  const selectedKey =
    preferredKey && available.includes(preferredKey) ? preferredKey : available[0];
  for (const key of available) {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = key;
    select.appendChild(option);
  }
  select.value = selectedKey;

  select.addEventListener("change", () => {
    refreshExtraSelectOptions();
    validateExtraRowFile(node).catch((err) => {
      pushToast({
        title: "Extra input validation error",
        message: err.message,
        kind: "warning",
        ttlMs: 7000,
      });
    });
  });
  const fileInput = node.querySelector(".extra-file");
  const infoBtn = node.querySelector(".extra-info-btn");
  infoBtn.addEventListener("click", () => {
    const payload = readHelpPayload(infoBtn);
    if (payload) {
      showInfoTooltip(payload);
    }
  });
  fileInput.addEventListener("change", async () => {
    syncExtraRowMeta(node);
    await validateExtraRowFile(node);
  });
  removeBtn.addEventListener("click", () => {
    node.remove();
    updateExtrasEmptyState();
    refreshExtraSelectOptions();
  });

  $("extras-list").appendChild(node);
  updateExtrasEmptyState();
  refreshExtraSelectOptions();
  syncExtraRowMeta(node);
}

function fillSelect(id, values) {
  const select = $(id);
  select.innerHTML = "";
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }
}

function collectRuns() {
  const cards = Array.from(document.querySelectorAll(".run-card"));
  if (!cards.length) {
    throw new Error("At least one run is required.");
  }

  const seen = new Set();
  const runs = [];
  cards.forEach((card, idx) => {
    const runId = card.querySelector(".run-id").value.trim();
    const toolId = card.querySelector(".tool-id").value;
    const paramsRaw = card.querySelector(".params-json").value;

    if (!runId) {
      throw new Error(`Run ${idx + 1}: run_id is required.`);
    }
    if (seen.has(runId)) {
      throw new Error(`Duplicate run_id: ${runId}`);
    }
    seen.add(runId);

    const params = parseJsonOrThrow(paramsRaw, `Run ${idx + 1} params`);

    runs.push({
      run_id: runId,
      tool_id: toolId,
      params,
    });
  });
  return runs;
}

function buildDatasetConfig() {
  const datasetId = $("dataset-id").value.trim();
  if (!datasetId) {
    throw new Error("dataset_id is required.");
  }

  return {
    dataset: {
      id: datasetId,
      column_kind: $("column-kind").value,
      expression_profile: $("expression-profile").value,
    },
    options: buildOptions(),
  };
}

function buildOptions() {
  return {
    output_dir: $("output-dir").value.trim() || "./inferred_networks_v2",
    max_cores: Number($("max-cores").value),
    max_ram_gb: $("max-ram").value.trim() ? Number($("max-ram").value) : null,
    planner: $("planner").value,
    planner_time_limit_seconds: Number($("planner-time").value),
    progress_poll_seconds: Number($("progress-poll").value),
    strict: $("strict").checked,
  };
}

function buildPreflightFormData(config) {
  const formData = new FormData();
  formData.append("config", JSON.stringify(config));

  const expressionInput = $("expression-file");
  if (!expressionInput.files || !expressionInput.files[0]) {
    throw new Error("Expression matrix file is required.");
  }
  formData.append("expression_file", expressionInput.files[0]);

  const seenExtraKeys = new Set();
  getExtraRows().forEach((row) => {
    const key = row.querySelector(".extra-key").value;
    const input = row.querySelector(".extra-file");
    if (!key) {
      return;
    }
    if (seenExtraKeys.has(key)) {
      throw new Error(`Optional input '${key}' is duplicated.`);
    }
    seenExtraKeys.add(key);
    if (input.files && input.files[0]) {
      formData.append(`extra__${key}`, input.files[0]);
    }
  });

  return formData;
}

function freezeActions(disabled) {
  const ids = [
    "analyze-btn",
    "plan-btn",
    "execute-btn",
    "add-all-tools-btn",
    "clear-runs-btn",
    "step-1-next-btn",
    "step-2-next-btn",
    "refresh-files-btn",
    "download-bundle-btn",
  ];
  for (const id of ids) {
    const node = $(id);
    if (node) {
      node.disabled = disabled;
    }
  }
}

function resetPlanView(message) {
  state.lastPlan = null;
  $("plan-summary").textContent = message || "No plan loaded yet.";
  $("plan-waves").innerHTML = "";
}

function resetNetworkView(message) {
  state.lastNetworkPreview = null;
  if (message) {
    $("file-preview-header").textContent = message;
  }
}

function resetFilesView(message) {
  state.selectedFilePath = null;
  $("files-summary").textContent = message || "No files loaded yet.";
  $("files-tree").innerHTML = "";
  $("file-preview-header").textContent = "Select a file to preview.";
  $("file-preview").innerHTML = "";
}

function renderRuntimeProgress(runtimeProgress = null) {
  const root = $("runtime-progress");
  if (!runtimeProgress || !Array.isArray(runtimeProgress.tools) || !runtimeProgress.tools.length) {
    root.textContent = "No runtime progress yet.";
    return;
  }
  root.innerHTML = "";
  const tools = [...runtimeProgress.tools].sort((a, b) => String(a.run_id).localeCompare(String(b.run_id)));

  const summary = runtimeProgress.summary || {};
  const header = document.createElement("div");
  header.className = "preflight-list-line";
  header.textContent =
    `total=${summary.total ?? tools.length} | running=${summary.running ?? 0} | completed=${summary.completed ?? 0} | failed=${summary.failed ?? 0}`;
  root.appendChild(header);

  for (const tool of tools) {
    const row = document.createElement("article");
    row.className = "runtime-progress-row";

    const head = document.createElement("div");
    head.className = "runtime-progress-head";
    const left = document.createElement("span");
    left.textContent = `${tool.run_id} · ${tool.status || "unknown"} · ${tool.phase || "-"}`;
    const right = document.createElement("span");
    right.textContent = `${Number(tool.percent || 0)}%`;
    head.appendChild(left);
    head.appendChild(right);
    row.appendChild(head);

    const bar = document.createElement("div");
    bar.className = "runtime-progress-bar";
    const fill = document.createElement("div");
    fill.className = "runtime-progress-fill";
    fill.classList.add(`status-${String(tool.status || "pending").toLowerCase()}`);
    fill.style.width = `${Math.max(0, Math.min(100, Number(tool.percent || 0)))}%`;
    bar.appendChild(fill);
    row.appendChild(bar);

    const msg = document.createElement("div");
    msg.className = "preflight-list-line";
    msg.textContent = String(tool.message || "").trim() || "No message";
    row.appendChild(msg);

    root.appendChild(row);
  }
}

function _pushRuntimeFailureToasts(runtimeProgress = null) {
  if (!runtimeProgress || !Array.isArray(runtimeProgress.tools)) {
    return;
  }
  for (const item of runtimeProgress.tools) {
    const runId = String(item?.run_id || "").trim();
    const status = String(item?.status || "").trim().toLowerCase();
    if (!runId || status !== "failed") {
      continue;
    }
    if (state.notifiedFailures.has(runId)) {
      continue;
    }
    state.notifiedFailures.add(runId);
    const message = String(item?.message || "").trim() || "Tool execution failed.";
    pushToast({
      title: `Tool failed: ${runId}`,
      message,
      kind: "error",
      ttlMs: 9000,
    });
  }
}

function renderExecutionAlerts(job = null, runReport = null) {
  const root = $("execution-alerts");
  if (!root) {
    return;
  }
  root.innerHTML = "";

  const errors = [];
  const warnings = [];
  if (runReport && Array.isArray(runReport.warnings)) {
    warnings.push(...runReport.warnings.map((x) => String(x)).filter(Boolean));
  }

  const failedMap = runReport?.tools?.failed;
  if (failedMap && typeof failedMap === "object") {
    for (const [runId, reason] of Object.entries(failedMap)) {
      errors.push(`${runId}: ${String(reason || "failed")}`);
    }
  }

  const jobError = String(job?.error || "").trim();
  if (jobError) {
    errors.push(jobError);
    const signature = `${job?.job_id || ""}:${jobError}`;
    if (state.notifiedJobError !== signature) {
      state.notifiedJobError = signature;
      pushToast({
        title: "Job failed",
        message: jobError,
        kind: "error",
        ttlMs: 10000,
      });
    }
  }

  if (!errors.length && !warnings.length) {
    root.textContent = "No execution errors or warnings.";
    return;
  }

  const title = document.createElement("div");
  title.className = "execution-alerts-title";
  title.textContent = `Execution alerts: ${errors.length} error(s), ${warnings.length} warning(s)`;
  root.appendChild(title);

  for (const message of errors.slice(0, 8)) {
    const line = document.createElement("div");
    line.className = "execution-alert error";
    line.textContent = message;
    root.appendChild(line);
  }
  for (const message of warnings.slice(0, 8)) {
    const line = document.createElement("div");
    line.className = "execution-alert warning";
    line.textContent = message;
    root.appendChild(line);
  }

  const hiddenErrors = Math.max(0, errors.length - 8);
  const hiddenWarnings = Math.max(0, warnings.length - 8);
  if (hiddenErrors || hiddenWarnings) {
    const more = document.createElement("div");
    more.className = "execution-alert";
    more.textContent = `... and ${hiddenErrors} more error(s), ${hiddenWarnings} more warning(s)`;
    root.appendChild(more);
  }
}

function renderFilePreview(payload) {
  const previewRoot = $("file-preview");
  previewRoot.innerHTML = "";
  if (!payload || typeof payload !== "object") {
    $("file-preview-header").textContent = "No preview available.";
    return;
  }

  const viewer = payload.viewer || "none";
  $("file-preview-header").textContent = `${payload.path || "-"} · ${viewer}`;

  if (viewer === "json" || viewer === "text" || viewer === "plan" || viewer === "network") {
    const pre = document.createElement("pre");
    pre.textContent = payload.text || payload.note || "No text preview.";
    previewRoot.appendChild(pre);
    return;
  }

  const renderTable = () => {
    const table = document.createElement("table");
    table.className = "preview-table";

    const headers = Array.isArray(payload.headers) ? payload.headers : [];
    const thead = document.createElement("thead");
    const trHead = document.createElement("tr");
    for (const header of headers) {
      const th = document.createElement("th");
      th.textContent = String(header);
      trHead.appendChild(th);
    }
    thead.appendChild(trHead);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    const rows = Array.isArray(payload.rows) ? payload.rows : [];
    for (const row of rows) {
      const tr = document.createElement("tr");
      for (const cell of row) {
        const td = document.createElement("td");
        td.textContent = String(cell);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    previewRoot.appendChild(table);

    if (payload.truncated) {
      const note = document.createElement("div");
      note.className = "muted-box";
      note.textContent = `Preview truncated. Showing ${rows.length} of ${payload.total_rows} row(s).`;
      previewRoot.appendChild(note);
    }
  };

  if (viewer === "table_csv" || viewer === "table_tsv") {
    renderTable();
    return;
  }

  if (viewer === "network_table_csv" || viewer === "network_table_tsv") {
    const networkPreview = payload.network_preview || null;
    if (networkPreview && Array.isArray(networkPreview.edges) && networkPreview.edges.length) {
      const graphHost = document.createElement("div");
      graphHost.className = "inline-network-plot";
      graphHost.id = "file-network-table-plot";
      previewRoot.appendChild(graphHost);
      if (window.Plotly) {
        const graph = _networkTraces(networkPreview);
        window.Plotly.react(graphHost.id, graph.traces, graph.layout, graph.config);
      } else {
        const pre = document.createElement("pre");
        pre.textContent = "Plotly is not available in this browser session.";
        previewRoot.appendChild(pre);
      }
    }
    renderTable();
    return;
  }

  const pre = document.createElement("pre");
  pre.textContent = "Preview is not available for this file type.";
  previewRoot.appendChild(pre);
}

function _entryName(path) {
  const normalized = String(path || "").replace(/^\/+/, "");
  const idx = normalized.lastIndexOf("/");
  return idx >= 0 ? normalized.slice(idx + 1) : normalized;
}

function _entryParent(path) {
  const normalized = String(path || "").replace(/^\/+/, "");
  const idx = normalized.lastIndexOf("/");
  return idx >= 0 ? normalized.slice(0, idx) : "";
}

function _buildEntriesTree(entries) {
  const root = {
    path: "",
    kind: "dir",
    name: "",
    children: [],
  };
  const nodes = new Map([["", root]]);

  const ensureDir = (dirPath) => {
    const normalized = String(dirPath || "").replace(/^\/+/, "");
    if (nodes.has(normalized)) {
      return nodes.get(normalized);
    }

    const parentPath = _entryParent(normalized);
    const parent = ensureDir(parentPath);
    const node = {
      path: normalized,
      kind: "dir",
      name: _entryName(normalized),
      size_bytes: null,
      viewer: "none",
      visualizable: false,
      children: [],
    };
    nodes.set(normalized, node);
    parent.children.push(node);
    return node;
  };

  const sorted = [...entries].sort((a, b) => String(a.path).localeCompare(String(b.path)));
  for (const entry of sorted) {
    const path = String(entry.path || "").replace(/^\/+/, "");
    if (!path) {
      continue;
    }

    const parent = ensureDir(_entryParent(path));
    const existing = nodes.get(path);
    const nextNode = {
      path,
      kind: entry.kind === "dir" ? "dir" : "file",
      name: _entryName(path),
      size_bytes: entry.size_bytes ?? null,
      viewer: entry.viewer || "none",
      visualizable: Boolean(entry.visualizable),
      children: existing?.children || [],
    };

    if (!existing) {
      parent.children.push(nextNode);
    }
    nodes.set(path, nextNode);
  }

  const sortChildren = (node) => {
    node.children.sort((a, b) => {
      const dirWeight = (a.kind === "dir" ? 0 : 1) - (b.kind === "dir" ? 0 : 1);
      if (dirWeight !== 0) {
        return dirWeight;
      }
      return String(a.name).localeCompare(String(b.name));
    });
    for (const child of node.children) {
      if (child.kind === "dir") {
        sortChildren(child);
      }
    }
  };
  sortChildren(root);
  return root;
}

function _renderTreeNode({ node, depth, mode }) {
  const tree = $("files-tree");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "file-node";
  if (node.kind === "dir") {
    button.classList.add("dir");
  }
  if (node.visualizable) {
    button.classList.add("visualizable");
  }
  if (node.path === state.selectedFilePath) {
    button.classList.add("selected");
  }

  button.style.paddingLeft = `${0.65 + depth * 1.05}rem`;
  button.title = node.path;

  const labelSpan = document.createElement("span");
  labelSpan.className = "node-label";

  const toggleSpan = document.createElement("span");
  toggleSpan.className = "toggle-glyph";
  const kindSpan = document.createElement("span");
  kindSpan.className = "kind-glyph";
  const nameSpan = document.createElement("span");
  nameSpan.className = "node-name";
  nameSpan.textContent = node.name;

  if (node.kind === "dir") {
    const collapsed = state.collapsedDirs.has(node.path);
    toggleSpan.textContent = collapsed ? "▸" : "▾";
    kindSpan.textContent = "📁";
    labelSpan.appendChild(toggleSpan);
    labelSpan.appendChild(kindSpan);
    labelSpan.appendChild(nameSpan);
  } else {
    toggleSpan.textContent = " ";
    kindSpan.textContent = "📄";
    labelSpan.appendChild(toggleSpan);
    labelSpan.appendChild(kindSpan);
    labelSpan.appendChild(nameSpan);
  }
  button.appendChild(labelSpan);

  const metaBits = [];
  if (node.kind === "file") {
    metaBits.push(formatBytes(node.size_bytes));
    if (node.viewer && node.viewer !== "none") {
      metaBits.push(node.viewer);
    }
  } else {
    metaBits.push(`${node.children.length} item(s)`);
  }
  if (metaBits.length) {
    const metaSpan = document.createElement("span");
    metaSpan.className = "meta";
    metaSpan.textContent = metaBits.join(" · ");
    button.appendChild(metaSpan);
  }

  if (node.kind === "dir") {
    button.addEventListener("click", () => {
      if (state.collapsedDirs.has(node.path)) {
        state.collapsedDirs.delete(node.path);
      } else {
        state.collapsedDirs.add(node.path);
      }
      renderFiles(state.filesEntries, mode);
    });
  } else {
    button.addEventListener("click", async () => {
      state.selectedFilePath = node.path;
      renderFiles(state.filesEntries, mode);
      try {
        await openFileEntry(node, mode);
      } catch (err) {
        pushToast({ title: "File preview error", message: err.message, kind: "warning", ttlMs: 7000 });
      }
    });
  }
  tree.appendChild(button);

  if (node.kind === "dir" && !state.collapsedDirs.has(node.path)) {
    for (const child of node.children) {
      _renderTreeNode({
        node: child,
        depth: depth + 1,
        mode,
      });
    }
  }
}

function renderFiles(entries, mode) {
  state.filesEntries = Array.isArray(entries) ? [...entries] : [];
  state.filesMode = mode;

  const tree = $("files-tree");
  tree.innerHTML = "";
  const list = state.filesEntries;
  const filesCount = list.filter((item) => item.kind === "file").length;
  const dirsCount = list.filter((item) => item.kind === "dir").length;
  $("files-summary").textContent = `mode=${mode} | files=${filesCount} | dirs=${dirsCount}`;

  if (!list.length) {
    const empty = document.createElement("div");
    empty.className = "muted-box";
    empty.textContent = "No files available for this job yet.";
    tree.appendChild(empty);
    return;
  }

  const root = _buildEntriesTree(list);
  for (const child of root.children) {
    _renderTreeNode({
      node: child,
      depth: 0,
      mode,
    });
  }
}

async function fetchFileContent(jobId, virtualPath, mode) {
  const response = await fetch(
    `/api/infer-network-v2/jobs/${jobId}/file-content?mode=${encodeURIComponent(mode)}&path=${encodeURIComponent(
      virtualPath
    )}&max_network_edges=${NETWORK_PREVIEW_MAX_EDGES}`
  );
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || `Failed to load file preview (${response.status})`);
  }
  return payload;
}

async function openFileEntry(entry, mode) {
  if (!state.jobId) {
    return;
  }
  if (!entry || entry.kind !== "file") {
    return;
  }

  if (entry.viewer === "plan") {
    const plan = state.lastPlan || (await fetchPlan(state.jobId));
    renderPlanInlinePreview(plan, entry.path);
    return;
  }

  const preview = await fetchFileContent(state.jobId, entry.path, mode);
  renderFilePreview(preview);
}

async function fetchFiles(jobId) {
  const mode = currentBundleMode();
  const response = await fetch(`/api/infer-network-v2/jobs/${jobId}/files?mode=${encodeURIComponent(mode)}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || `Failed to load files (${response.status})`);
  }
  const entries = Array.isArray(payload.entries) ? payload.entries : [];
  if (state.loadedFilesKey === null) {
    state.collapsedDirs = new Set(
      entries
        .filter((item) => item.kind === "dir" && item.path)
        .map((item) => String(item.path))
    );
  }
  renderFiles(entries, mode);
  state.loadedFilesKey = `${jobId}:${mode}:${entries.length}`;

  const currentExists = entries.some(
    (item) => item.kind === "file" && String(item.path) === String(state.selectedFilePath || "")
  );
  if (currentExists && state.selectedFilePath) {
    const selected = entries.find(
      (item) => item.kind === "file" && String(item.path) === String(state.selectedFilePath)
    );
    if (selected) {
      try {
        await openFileEntry(selected, mode);
      } catch (err) {
        pushToast({ title: "File preview error", message: err.message, kind: "warning", ttlMs: 7000 });
      }
    }
    return;
  }

  const preferred = entries.find(
    (item) => item.kind === "file" && String(item.path).toLowerCase().endsWith("run/merged_network_normalized.csv")
  );
  const fallback = entries.find((item) => item.kind === "file" && item.visualizable);
  const target = preferred || fallback || null;
  if (target) {
    state.selectedFilePath = target.path;
    renderFiles(entries, mode);
    try {
      await openFileEntry(target, mode);
    } catch (err) {
      pushToast({ title: "File preview error", message: err.message, kind: "warning", ttlMs: 7000 });
    }
  }
}

function renderPlan(plan) {
  if (!plan || typeof plan !== "object") {
    resetPlanView("No plan available for this job yet.");
    state.lastPlan = null;
    return;
  }
  state.lastPlan = plan;

  const planner = plan.planner || {};
  const totals = plan.totals || {};
  const lines = [
    `run_id: ${plan.run_id || "-"}`,
    `planner: requested=${planner.requested || "-"}, used=${planner.used || "-"}`,
    `tasks_total: ${totals.tasks_total ?? "-"}`,
    `waves_total: ${totals.waves_total ?? "-"}`,
    `threads_peak: ${totals.threads_peak ?? "-"}`,
    `ram_peak_gb: ${totals.ram_peak_gb ?? "-"}`,
    `eta_total_seconds: ${plan.eta_total_seconds ?? "-"}`,
  ];
  $("plan-summary").textContent = lines.join("\n");

  const wavesRoot = $("plan-waves");
  wavesRoot.innerHTML = "";
  const waves = Array.isArray(plan.waves) ? plan.waves : [];
  if (!waves.length) {
    wavesRoot.textContent = "This plan has no waves.";
    return;
  }

  for (const wave of waves) {
    const card = document.createElement("article");
    card.className = "wave-card";

    const head = document.createElement("div");
    head.className = "wave-head";
    const headParts = [
      { label: `Wave ${wave.index}`, cls: "wave-title" },
      { label: `tasks=${Array.isArray(wave.tasks) ? wave.tasks.length : 0}` },
      { label: `cores=${wave.threads_used ?? "-"}` },
      { label: `ram=${wave.ram_gb_used ?? "-"}GB` },
      { label: `eta=${wave.eta_seconds ?? "-"}s` },
      { label: `window=[${wave.eta_start_seconds ?? "-"}, ${wave.eta_end_seconds ?? "-"}]` },
    ];
    for (const part of headParts) {
      const span = document.createElement("span");
      if (part.cls) {
        span.className = part.cls;
      }
      span.textContent = part.label;
      head.appendChild(span);
    }

    const table = document.createElement("table");
    table.className = "wave-table";
    table.innerHTML =
      "<thead><tr>" +
      "<th>run_id</th><th>threads</th><th>ram_gb</th><th>eta_s</th><th>source</th><th>note</th>" +
      "</tr></thead>";

    const tbody = document.createElement("tbody");
    const tasks = Array.isArray(wave.tasks) ? wave.tasks : [];
    for (const task of tasks) {
      const tr = document.createElement("tr");
      const cells = [
        task.run_id || task.tool_id || "-",
        task.threads ?? "-",
        task.ram_gb ?? "-",
        task.eta_seconds ?? "-",
        task.eta_source || "-",
        task.note || "",
      ];
      for (const value of cells) {
        const td = document.createElement("td");
        td.textContent = String(value);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);

    card.appendChild(head);
    card.appendChild(table);
    wavesRoot.appendChild(card);
  }
}

function circularLayout(nodes) {
  const total = nodes.length;
  const radius = Math.max(1, Math.sqrt(total) * 2.1);
  const positions = new Map();

  nodes.forEach((node, idx) => {
    const angle = (2 * Math.PI * idx) / Math.max(1, total);
    positions.set(node.id, {
      x: radius * Math.cos(angle),
      y: radius * Math.sin(angle),
    });
  });

  return positions;
}

function _networkTraces(preview) {
  const nodes = Array.isArray(preview?.nodes) ? preview.nodes : [];
  const edges = Array.isArray(preview?.edges) ? preview.edges : [];
  const positions = circularLayout(nodes);

  const edgeX = [];
  const edgeY = [];
  for (const edge of edges) {
    const srcPos = positions.get(edge.source);
    const tgtPos = positions.get(edge.target);
    if (!srcPos || !tgtPos) {
      continue;
    }
    edgeX.push(srcPos.x, tgtPos.x, null);
    edgeY.push(srcPos.y, tgtPos.y, null);
  }

  const nodeX = [];
  const nodeY = [];
  const nodeText = [];
  const nodeSize = [];
  const nodeColor = [];
  for (const node of nodes) {
    const pos = positions.get(node.id);
    if (!pos) {
      continue;
    }
    const inDegree = Number(node.in_degree || 0);
    const outDegree = Number(node.out_degree || 0);
    const degree = inDegree + outDegree;
    nodeX.push(pos.x);
    nodeY.push(pos.y);
    nodeSize.push(8 + Math.log2(1 + degree) * 7);
    nodeColor.push(outDegree - inDegree);
    nodeText.push(
      `${node.id}<br>` +
        `in=${inDegree}, out=${outDegree}<br>` +
        `weight_sum=${Number(node.weight_sum || 0).toFixed(4)}`
    );
  }

  return {
    traces: [
      {
        type: "scattergl",
        mode: "lines",
        x: edgeX,
        y: edgeY,
        line: { width: 0.7, color: "rgba(120,120,120,0.35)" },
        hoverinfo: "skip",
        showlegend: false,
      },
      {
        type: "scattergl",
        mode: "markers",
        x: nodeX,
        y: nodeY,
        text: nodeText,
        hovertemplate: "%{text}<extra></extra>",
        marker: {
          size: nodeSize,
          color: nodeColor,
          colorscale: "RdBu",
          reversescale: true,
          line: { width: 0.5, color: "#0f172a" },
          colorbar: {
            title: "out - in",
          },
        },
        showlegend: false,
      },
    ],
    layout: {
      margin: { l: 20, r: 20, t: 20, b: 20 },
      xaxis: { visible: false },
      yaxis: { visible: false, scaleanchor: "x", scaleratio: 1 },
      paper_bgcolor: "rgba(255,255,255,0)",
      plot_bgcolor: "rgba(255,255,255,0)",
      hovermode: "closest",
    },
    config: {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["select2d", "lasso2d"],
    },
  };
}

function renderPlanInlinePreview(plan, virtualPath) {
  const previewRoot = $("file-preview");
  previewRoot.innerHTML = "";
  $("file-preview-header").textContent = `${virtualPath} · plan`;

  if (!plan || typeof plan !== "object") {
    const pre = document.createElement("pre");
    pre.textContent = "No plan is available for this job yet.";
    previewRoot.appendChild(pre);
    return;
  }

  const summary = document.createElement("div");
  summary.className = "muted-box plan-inline-summary";
  summary.textContent = $("plan-summary").textContent || "Plan loaded.";
  previewRoot.appendChild(summary);

  const wavesHost = document.createElement("div");
  wavesHost.className = "inline-plan-waves";
  const waves = Array.isArray(plan.waves) ? plan.waves : [];
  if (!waves.length) {
    const pre = document.createElement("pre");
    pre.textContent = "This plan has no waves.";
    previewRoot.appendChild(pre);
    return;
  }
  for (const wave of waves) {
    const card = document.createElement("article");
    card.className = "wave-card";
    const head = document.createElement("div");
    head.className = "wave-head";
    head.innerHTML = `<span class=\"wave-title\">Wave ${wave.index}</span><span>tasks=${Array.isArray(
      wave.tasks
    ) ? wave.tasks.length : 0}</span><span>cores=${wave.threads_used ?? "-"}</span><span>ram=${
      wave.ram_gb_used ?? "-"
    }GB</span>`;
    card.appendChild(head);
    const table = document.createElement("table");
    table.className = "wave-table";
    table.innerHTML =
      "<thead><tr>" +
      "<th>run_id</th><th>threads</th><th>ram_gb</th><th>eta_s</th><th>source</th><th>note</th>" +
      "</tr></thead>";
    const tbody = document.createElement("tbody");
    const tasks = Array.isArray(wave.tasks) ? wave.tasks : [];
    for (const task of tasks) {
      const tr = document.createElement("tr");
      const cells = [
        task.run_id || task.tool_id || "-",
        task.threads ?? "-",
        task.ram_gb ?? "-",
        task.eta_seconds ?? "-",
        task.eta_source || "-",
        task.note || "",
      ];
      for (const value of cells) {
        const td = document.createElement("td");
        td.textContent = String(value);
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    card.appendChild(table);
    wavesHost.appendChild(card);
  }
  previewRoot.appendChild(wavesHost);
}

function renderNetworkInlinePreview(preview, virtualPath) {
  const previewRoot = $("file-preview");
  previewRoot.innerHTML = "";
  $("file-preview-header").textContent = `${virtualPath} · network`;

  if (!preview || !Array.isArray(preview.edges) || !preview.edges.length) {
    const pre = document.createElement("pre");
    pre.textContent = "No merged network preview available yet.";
    previewRoot.appendChild(pre);
    return;
  }

  const nodes = Array.isArray(preview.nodes) ? preview.nodes : [];
  const stats = document.createElement("div");
  stats.className = "muted-box";
  stats.textContent =
    `source: ${preview.path || "-"}\n` +
    `total_edges_in_file: ${preview.total_edges ?? "-"}\n` +
    `edges_returned: ${preview.returned_edges ?? preview.edges.length}\n` +
    `preview_limit: ${preview.max_edges ?? "-"}\n` +
    `score_range: [${preview.score_min ?? "-"}, ${preview.score_max ?? "-"}]\n` +
    `nodes_in_preview: ${nodes.length}`;
  previewRoot.appendChild(stats);

  const plotId = "file-network-plot";
  const plot = document.createElement("div");
  plot.className = "inline-network-plot";
  plot.id = plotId;
  previewRoot.appendChild(plot);

  if (!window.Plotly) {
    const pre = document.createElement("pre");
    pre.textContent = "Plotly is not available in this browser session.";
    previewRoot.appendChild(pre);
    return;
  }

  const graph = _networkTraces(preview);
  window.Plotly.react(plotId, graph.traces, graph.layout, graph.config);
}

async function fetchPlan(jobId) {
  const response = await fetch(`/api/infer-network-v2/jobs/${jobId}/plan`);
  if (!response.ok) {
    throw new Error(`Failed to load plan (${response.status})`);
  }
  const payload = await response.json();
  renderPlan(payload.plan);
  return payload.plan;
}

async function fetchNetworkPreview(jobId) {
  const response = await fetch(
    `/api/infer-network-v2/jobs/${jobId}/network-preview?max_edges=${NETWORK_PREVIEW_MAX_EDGES}`
  );
  if (!response.ok) {
    throw new Error(`Failed to load network preview (${response.status})`);
  }
  const payload = await response.json();
  state.lastNetworkPreview = payload.network_preview || null;
  state.loadedNetworkKey = `${jobId}:${NETWORK_PREVIEW_MAX_EDGES}`;
  return state.lastNetworkPreview;
}

async function refreshArtifacts(job) {
  if (!job || !job.job_id) {
    return;
  }

  if (job.plan_path) {
    const planKey = `${job.job_id}:${job.plan_path}`;
    if (state.loadedPlanKey !== planKey) {
      await fetchPlan(job.job_id);
      state.loadedPlanKey = planKey;
    }
  }

  if ((job.stage === "executed" && job.status === "completed") || job.status === "failed") {
    const desiredNetworkKey = `${job.job_id}:${NETWORK_PREVIEW_MAX_EDGES}`;
    if (state.loadedNetworkKey !== desiredNetworkKey) {
      await fetchNetworkPreview(job.job_id);
    }
  }

  if (job.status !== "queued") {
    const mode = currentBundleMode();
    const desiredFilesKey = `${job.job_id}:${mode}:${job.status}:${job.run_dir || ""}`;
    if (state.loadedFilesKey !== desiredFilesKey) {
      await fetchFiles(job.job_id);
      state.loadedFilesKey = desiredFilesKey;
    }
  }
}

async function pollJob(jobId) {
  const response = await fetch(`/api/infer-network-v2/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(`Failed to load job status (${response.status})`);
  }
  const payload = await response.json();
  const job = payload.job;
  const runReport = payload.run_report;
  const preflightReport = payload.preflight_report;
  const runtimeProgress = payload.runtime_progress;
  state.stage = job.stage || state.stage;
  state.runtimeProgress = runtimeProgress || null;
  if (job.stage === "planned" && state.activeStep < 3) {
    setActiveStep(2, { scroll: false });
  }
  if (
    job.status === "running" &&
    (job.stage === "planned" || job.stage === "executed") &&
    state.activeStep < 3
  ) {
    setActiveStep(3, { scroll: false });
  }

  updateToolEligibilityView(preflightReport);
  renderRuntimeProgress(runtimeProgress);
  _pushRuntimeFailureToasts(runtimeProgress);
  renderExecutionAlerts(job, runReport);

  syncActionButtons(job);
  await refreshArtifacts(job);

  if (job.status === "completed" || job.status === "failed") {
    freezeActions(false);
    syncActionButtons(job);
    if (state.pollTimer) {
      window.clearInterval(state.pollTimer);
      state.pollTimer = null;
    }
  }
}

function syncActionButtons(job = null) {
  const analyzeBtn = $("analyze-btn");
  const planBtn = $("plan-btn");
  const executeBtn = $("execute-btn");
  const addAllBtn = $("add-all-tools-btn");
  const clearRunsBtn = $("clear-runs-btn");
  const step1NextBtn = $("step-1-next-btn");
  const step2NextBtn = $("step-2-next-btn");

  if (!job) {
    analyzeBtn.disabled = false;
    planBtn.disabled = true;
    executeBtn.disabled = true;
    addAllBtn.disabled = true;
    clearRunsBtn.disabled = true;
    step1NextBtn.disabled = true;
    step2NextBtn.disabled = true;
    setStepState(1, "ready");
    setStepState(2, "blocked");
    setStepState(3, "blocked");
    return;
  }

  const isBusy = job.status === "queued" || job.status === "running";
  const preflightReady = ["preflight_ok", "planned", "executed"].includes(job.stage || "");
  const planReady = ["planned", "executed"].includes(job.stage || "");
  const runReady = String(job.stage || "") === "planned";

  analyzeBtn.disabled = isBusy;
  planBtn.disabled = isBusy || !preflightReady;
  executeBtn.disabled = isBusy || !runReady;
  addAllBtn.disabled = isBusy || !preflightReady;
  clearRunsBtn.disabled = isBusy || !preflightReady;
  step1NextBtn.disabled = !preflightReady || isBusy;
  step2NextBtn.disabled = !planReady || isBusy;

  const step1State = preflightReady ? "ready" : isBusy ? "running" : "blocked";
  const step2State = planReady ? "ready" : preflightReady ? (isBusy ? "running" : "ready") : "blocked";
  const step3State = job.stage === "executed" ? "ready" : runReady ? (isBusy ? "running" : "ready") : "blocked";
  setStepState(1, step1State);
  setStepState(2, step2State);
  setStepState(3, step3State);
}

function updatePreflightSummary(preflightReport = null) {
  const viewEl = $("preflight-report-view");
  if (!preflightReport || !preflightReport.catalog) {
    viewEl.textContent = "No preflight report yet.";
    return;
  }
  const eligible = Array.isArray(preflightReport.catalog.eligible) ? preflightReport.catalog.eligible : [];
  const warning = Array.isArray(preflightReport.catalog.warning) ? preflightReport.catalog.warning : [];
  const blocked = Array.isArray(preflightReport.catalog.blocked) ? preflightReport.catalog.blocked : [];
  viewEl.innerHTML = "";

  const kpiGrid = document.createElement("div");
  kpiGrid.className = "preflight-grid";
  const kpis = [
    { label: "Dataset", value: String(preflightReport?.dataset?.dataset_id || "-") },
    { label: "Expression", value: `${preflightReport?.dataset?.genes ?? "-"} × ${preflightReport?.dataset?.columns ?? "-"}` },
    { label: "Eligible", value: String(eligible.length) },
    { label: "Warning", value: String(warning.length) },
    { label: "Blocked", value: String(blocked.length) },
  ];
  for (const item of kpis) {
    const card = document.createElement("article");
    card.className = "preflight-kpi";
    const strong = document.createElement("strong");
    strong.textContent = item.label;
    const span = document.createElement("span");
    span.textContent = item.value;
    card.appendChild(strong);
    card.appendChild(span);
    kpiGrid.appendChild(card);
  }
  viewEl.appendChild(kpiGrid);

  const validation = preflightReport.input_validation || {};
  const exprValidation = validation.expression_matrix || {};
  const extrasValidation = validation.extras || {};
  const validationList = document.createElement("section");
  validationList.className = "preflight-list";
  validationList.innerHTML = "<h4>Input Validation</h4>";
  const exprErrors = Array.isArray(exprValidation.errors) ? exprValidation.errors : [];
  const exprWarnings = Array.isArray(exprValidation.warnings) ? exprValidation.warnings : [];
  const exprDetail = exprErrors[0] || exprWarnings[0] || "";
  const exprLine = document.createElement("div");
  exprLine.className = "preflight-list-line";
  exprLine.textContent = `expression_matrix: ${exprValidation.status || "unknown"}${
    exprDetail ? ` (${exprDetail})` : ""
  }`;
  validationList.appendChild(exprLine);
  const extraKeys = Object.keys(extrasValidation).sort();
  for (const key of extraKeys) {
    const item = extrasValidation[key] || {};
    const status = item.status || "unknown";
    const errors = Array.isArray(item.errors) ? item.errors : [];
    const warns = Array.isArray(item.warnings) ? item.warnings : [];
    const detail = errors[0] || warns[0] || "";
    const line = document.createElement("div");
    line.className = "preflight-list-line";
    line.textContent = `${key}: ${status}${detail ? ` (${detail})` : ""}`;
    validationList.appendChild(line);
  }
  viewEl.appendChild(validationList);

  const warningsList = document.createElement("section");
  warningsList.className = "preflight-list";
  warningsList.innerHTML = "<h4>Warnings</h4>";
  const warnings = Array.isArray(preflightReport.warnings) ? preflightReport.warnings : [];
  if (!warnings.length) {
    const line = document.createElement("div");
    line.className = "preflight-list-line";
    line.textContent = "No warnings.";
    warningsList.appendChild(line);
  } else {
    for (const warningText of warnings.slice(0, 8)) {
      const line = document.createElement("div");
      line.className = "preflight-list-line";
      line.textContent = `• ${String(warningText)}`;
      warningsList.appendChild(line);
    }
    if (warnings.length > 8) {
      const line = document.createElement("div");
      line.className = "preflight-list-line";
      line.textContent = `... ${warnings.length - 8} more`;
      warningsList.appendChild(line);
    }
  }
  viewEl.appendChild(warningsList);

  const rawDetails = document.createElement("details");
  rawDetails.className = "preflight-list";
  const summaryNode = document.createElement("summary");
  summaryNode.textContent = "Raw preflight_report.json";
  rawDetails.appendChild(summaryNode);
  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(preflightReport, null, 2);
  rawDetails.appendChild(pre);
  viewEl.appendChild(rawDetails);
}

function _toolMessages(entry) {
  const reasons = Array.isArray(entry?.reasons) ? entry.reasons : [];
  const warnings = Array.isArray(entry?.warnings) ? entry.warnings : [];
  const out = [];
  for (const reason of reasons) {
    if (String(reason || "").trim()) {
      out.push(String(reason).trim());
    }
  }
  for (const warning of warnings) {
    if (String(warning || "").trim()) {
      out.push(String(warning).trim());
    }
  }
  return out;
}

function _toolSpecInfoPayload(tool) {
  const accepts = Array.isArray(tool?.accepts) ? tool.accepts : [];
  const requiredExtras = Array.isArray(tool?.required_extras) ? tool.required_extras : [];
  const optionalExtras = Array.isArray(tool?.optional_extras) ? tool.optional_extras : [];
  const publication = Array.isArray(tool?.publication) ? tool.publication : [];
  const firstAuthor = String(tool?.first_author || "").trim();
  const outputs = tool?.outputs && typeof tool.outputs === "object" ? tool.outputs : {};
  const progress = tool?.progress && typeof tool.progress === "object" ? tool.progress : {};

  const publicationLinks = publication.map((item) => ({
    label: String(item || "").trim(),
    url: String(item || "").trim(),
  }));
  return {
    title: tool?.name || tool?.tool_id || "Tool Info",
    description: "",
    fields: [
      { label: "Tool ID", value: tool?.tool_id || "-" },
      { label: "Assumes", value: tool?.assumes || "-" },
      { label: "Accepts", value: accepts.length ? accepts.join(", ") : "-" },
      { label: "Required extras", value: requiredExtras.length ? requiredExtras.join(", ") : "none" },
      { label: "Optional extras", value: optionalExtras.length ? optionalExtras.join(", ") : "none" },
      {
        label: "Outputs",
        value: `directed=${String(outputs.directed ?? "-")}, sign=${outputs.sign ?? "-"}, evidence=${outputs.evidence ?? "-"}`,
      },
      {
        label: "Progress",
        value: `${progress.kind || "-"}${progress.note ? ` (${String(progress.note)})` : ""}`,
      },
      {
        label: "Implementation",
        link: {
          label: String(tool?.implementation_url || "-"),
          url: String(tool?.implementation_url || ""),
        },
        value: tool?.implementation_url || "-",
      },
      { label: "Docker image", value: tool?.docker_image || "-" },
      { label: "First author", value: firstAuthor || "-" },
      {
        label: "Publication(s)",
        links: publicationLinks.length ? publicationLinks : [{ label: "-", url: "" }],
      },
    ],
    example: "",
  };
}

function _buildToolRequestIssueUrl() {
  const toolName = String($("tool-request-tool-name")?.value || "").trim();
  const doi = String($("tool-request-doi")?.value || "").trim();
  const repoUrl = String($("tool-request-repo")?.value || "").trim();
  const expectedInputs = String($("tool-request-inputs")?.value || "").trim();
  const expectedOutputs = String($("tool-request-outputs")?.value || "").trim();
  const notes = String($("tool-request-notes")?.value || "").trim();

  if (!toolName) {
    throw new Error("Tool Name is required to create the issue.");
  }

  const issueTitle = `[Tool Request] ${toolName}`;
  const bodyLines = [
    "## Tool Request",
    "",
    `- Tool name: ${toolName}`,
    `- DOI / publication: ${doi || "-"}`,
    `- Implementation repository: ${repoUrl || "-"}`,
    `- Expected inputs: ${expectedInputs || "-"}`,
    `- Expected outputs: ${expectedOutputs || "-"}`,
    "",
    "## Notes",
    notes || "-",
    "",
    "## Submitted From",
    "- GENECI GUI infer-network-v2",
  ];

  const params = new URLSearchParams();
  params.set("title", issueTitle);
  params.set("body", bodyLines.join("\n"));
  params.set("labels", "tool-request");

  return `https://github.com/AdrianSeguraOrtiz/GENECI/issues/new?${params.toString()}`;
}

function _populateToolIssueSelect() {
  const select = $("tool-issue-tool-id");
  if (!select) {
    return;
  }
  const tools = Array.isArray(state.bootstrap?.tools) ? [...state.bootstrap.tools] : [];
  tools.sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
  select.innerHTML = "";
  for (const tool of tools) {
    const option = document.createElement("option");
    option.value = String(tool.tool_id || "");
    option.textContent = String(tool.name || tool.tool_id || "");
    select.appendChild(option);
  }
}

function _buildToolIssueReportUrl() {
  const toolId = String($("tool-issue-tool-id")?.value || "").trim();
  const issueType = String($("tool-issue-type")?.value || "other").trim();
  const observed = String($("tool-issue-observed")?.value || "").trim();
  const expected = String($("tool-issue-expected")?.value || "").trim();
  const context = String($("tool-issue-context")?.value || "").trim();

  if (!toolId) {
    throw new Error("Select a tool to report.");
  }
  if (!observed) {
    throw new Error("Observed Behavior is required.");
  }
  const tool = toolById(toolId);
  const toolName = String(tool?.name || toolId);

  const issueTitle = `[Tool Catalog Issue] ${toolName} (${issueType})`;
  const bodyLines = [
    "## Tool Catalog Issue",
    "",
    `- tool_id: ${toolId}`,
    `- tool_name: ${toolName}`,
    `- issue_type: ${issueType}`,
    "",
    "## Observed",
    observed,
    "",
    "## Expected",
    expected || "-",
    "",
    "## Context",
    context || "-",
    "",
    "## Submitted From",
    "- GENECI GUI infer-network-v2",
  ];

  const params = new URLSearchParams();
  params.set("title", issueTitle);
  params.set("body", bodyLines.join("\n"));
  params.set("labels", "tool-catalog-issue");
  return `https://github.com/AdrianSeguraOrtiz/GENECI/issues/new?${params.toString()}`;
}

function _renderToolCatalogList(containerId, entries, kind) {
  const host = $(containerId);
  host.innerHTML = "";
  if (!entries.length) {
    const empty = document.createElement("div");
    empty.className = "muted-box";
    empty.textContent = "No tools in this group.";
    host.appendChild(empty);
    return;
  }

  const template = $("tool-catalog-item-template");
  for (const entry of entries) {
    const toolId = String(entry?.tool_id || "");
    const tool = toolById(toolId);
    if (!tool) {
      continue;
    }

    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".tool-item-name").textContent = tool.name;
    node.querySelector(".tool-item-badge").textContent = kind;
    node.querySelector(".tool-item-meta").textContent =
      String(tool.assumes || "").trim() || `tool_id=${tool.tool_id}`;
    const actions = node.querySelector(".tool-item-actions");

    const specBtn = document.createElement("button");
    specBtn.type = "button";
    specBtn.className = "secondary";
    specBtn.textContent = "Tool Info";
    specBtn.addEventListener("click", () => {
      showInfoTooltip(_toolSpecInfoPayload(tool));
    });

    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "Add Run";
    addBtn.className = "secondary";
    addBtn.addEventListener("click", () => {
      try {
        addRunCard({ tool_id: tool.tool_id });
      } catch (err) {
        pushToast({ title: "Run configuration error", message: err.message, kind: "error", ttlMs: 8000 });
      }
    });

    const infoBtn = document.createElement("button");
    infoBtn.type = "button";
    infoBtn.textContent = kind === "blocked" ? "Why Blocked" : "View Details";
    const messages = _toolMessages(entry);
    infoBtn.addEventListener("click", () => {
      showInfoTooltip({
        title: tool.name,
        description: messages.length ? messages.join("\n") : "No additional details.",
        example: "",
      });
    });

    if (kind === "blocked") {
      actions.appendChild(specBtn);
      actions.appendChild(infoBtn);
    } else if (kind === "warning") {
      actions.appendChild(specBtn);
      actions.appendChild(addBtn);
      actions.appendChild(infoBtn);
    } else {
      actions.appendChild(specBtn);
      actions.appendChild(addBtn);
    }
    host.appendChild(node);
  }
}

function updateToolEligibilityView(preflightReport = null) {
  state.preflightReport = preflightReport;
  updatePreflightSummary(preflightReport);

  const eligibleList = $("tools-eligible-list");
  const warningList = $("tools-warning-list");
  const blockedList = $("tools-blocked-list");

  if (!preflightReport || !preflightReport.catalog) {
    state.eligibleToolIds = null;
    $("eligible-count").textContent = "0";
    $("warning-count").textContent = "0";
    $("blocked-count").textContent = "0";
    eligibleList.innerHTML = "";
    warningList.innerHTML = "";
    blockedList.innerHTML = "";
    return;
  }

  const eligible = Array.isArray(preflightReport.catalog.eligible) ? preflightReport.catalog.eligible : [];
  const warning = Array.isArray(preflightReport.catalog.warning) ? preflightReport.catalog.warning : [];
  const blocked = Array.isArray(preflightReport.catalog.blocked) ? preflightReport.catalog.blocked : [];

  state.eligibleToolIds = [
    ...new Set(
      [...eligible, ...warning]
        .map((item) => String(item?.tool_id || "").trim())
        .filter(Boolean)
    ),
  ];

  $("eligible-count").textContent = String(eligible.length);
  $("warning-count").textContent = String(warning.length);
  $("blocked-count").textContent = String(blocked.length);

  _renderToolCatalogList("tools-eligible-list", eligible, "eligible");
  _renderToolCatalogList("tools-warning-list", warning, "warning");
  _renderToolCatalogList("tools-blocked-list", blocked, "blocked");
}

async function startPolling(jobId) {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
  }
  await pollJob(jobId);
  state.pollTimer = window.setInterval(() => {
    pollJob(jobId).catch((err) => {
      pushToast({ title: "Polling error", message: err.message, kind: "error", ttlMs: 7000 });
    });
  }, 1500);
}

async function submitPreflight() {
  try {
    const expressionStatus = $("expression-file-status");
    if (expressionStatus.classList.contains("err")) {
      throw new Error("Expression matrix is invalid. Fix it before submitting.");
    }
    const expressionInput = $("expression-file");
    if (!expressionInput.files || !expressionInput.files[0]) {
      throw new Error("Expression matrix file is required.");
    }
    freezeActions(true);
    const config = buildDatasetConfig();
    const formData = buildPreflightFormData(config);

    state.loadedPlanKey = null;
    state.loadedNetworkKey = null;
    state.loadedFilesKey = null;
    state.selectedFilePath = null;
    state.collapsedDirs.clear();
    state.eligibleToolIds = null;
    state.preflightReport = null;
    state.lastPlan = null;
    state.lastNetworkPreview = null;
    state.runtimeProgress = null;
    state.notifiedFailures.clear();
    state.notifiedJobError = "";
    setActiveStep(1, { scroll: false });
    $("runs-container").innerHTML = "";
    updateRunsEmptyState();
    updateToolEligibilityView(null);
    resetPlanView("Waiting for preflight/plan output...");
    resetNetworkView("Waiting for merged network output...");
    resetFilesView("Waiting for files...");
    renderRuntimeProgress(null);
    renderExecutionAlerts(null, null);
    const response = await fetch("/api/infer-network-v2/preflight", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Preflight submission failed");
    }

    state.jobId = payload.job_id;
    state.stage = "draft";
    setStepState(1, "running");
    setStepState(2, "blocked");
    setStepState(3, "blocked");
    pushToast({
      title: "Preflight submitted",
      message: `Job: ${payload.job_id}`,
      kind: "success",
      ttlMs: 4000,
    });

    await startPolling(state.jobId);
  } catch (err) {
    freezeActions(false);
    syncActionButtons();
    pushToast({ title: "Preflight error", message: err.message, kind: "error", ttlMs: 9000 });
  }
}

async function submitPlan() {
  try {
    if (!state.jobId) {
      throw new Error("Analyze inputs first.");
    }
    setActiveStep(2, { scroll: false });
    const runs = collectRuns();
    freezeActions(true);
    setStepState(2, "running");

    const response = await fetch("/api/infer-network-v2/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_id: state.jobId,
        runs,
        options: buildOptions(),
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Plan submission failed");
    }
    pushToast({
      title: "Plan submitted",
      message: `Job: ${payload.job_id}`,
      kind: "success",
      ttlMs: 4000,
    });
    await startPolling(state.jobId);
  } catch (err) {
    freezeActions(false);
    syncActionButtons();
    pushToast({ title: "Planning error", message: err.message, kind: "error", ttlMs: 9000 });
  }
}

async function submitRun() {
  try {
    if (!state.jobId) {
      throw new Error("No planned job found. Generate a plan first.");
    }
    setActiveStep(3, { scroll: false });
    freezeActions(true);
    setStepState(3, "running");

    const response = await fetch("/api/infer-network-v2/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_id: state.jobId,
        options: {
          progress_poll_seconds: Number($("progress-poll").value),
          strict: $("strict").checked,
        },
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Run submission failed");
    }
    pushToast({
      title: "Execution submitted",
      message: `Job: ${payload.job_id}`,
      kind: "success",
      ttlMs: 4000,
    });
    await startPolling(state.jobId);
  } catch (err) {
    freezeActions(false);
    syncActionButtons();
    pushToast({ title: "Execution error", message: err.message, kind: "error", ttlMs: 9000 });
  }
}

async function bootstrap() {
  const response = await fetch("/api/infer-network-v2/bootstrap");
  if (!response.ok) {
    throw new Error(`Failed to load bootstrap data (${response.status})`);
  }

  state.bootstrap = await response.json();
  fillSelect("column-kind", state.bootstrap.column_kinds);
  fillSelect("expression-profile", state.bootstrap.expression_profiles);
  _populateToolIssueSelect();
  syncExpressionHelpTooltip();
  initExpressionDropzone();
  await handleExpressionSelected(null);
  updateExtrasEmptyState();
  updateRunsEmptyState();
  updateToolEligibilityView(null);
  resetPlanView("No plan loaded yet.");
  resetNetworkView();
  resetFilesView("No files loaded yet.");
  renderRuntimeProgress(null);
  renderExecutionAlerts(null, null);
  state.notifiedFailures.clear();
  state.notifiedJobError = "";
  setActiveStep(1, { scroll: false });
  syncActionButtons();
}

function bindEvents() {
  const canOpenStep = (stepNumber) => {
    if (stepNumber <= 1) {
      return true;
    }
    if (stepNumber === 2) {
      return ["preflight_ok", "planned", "executed"].includes(String(state.stage || ""));
    }
    if (stepNumber === 3) {
      return ["planned", "executed"].includes(String(state.stage || ""));
    }
    return false;
  };

  const tryOpenStep = (stepNumber) => {
    if (!canOpenStep(stepNumber)) {
      pushToast({
        title: "Step not available",
        message: `Step ${stepNumber} is not available yet.`,
        kind: "warning",
        ttlMs: 5000,
      });
      return;
    }
    setActiveStep(stepNumber);
  };

  $("expression-info-btn").addEventListener("click", () => {
    const payload = readHelpPayload($("expression-info-btn"));
    if (payload) {
      showInfoTooltip(payload);
    }
  });
  $("add-optional-input-btn").addEventListener("click", () => addOptionalExtraRow());
  $("add-all-tools-btn").addEventListener("click", () => {
    try {
      const existingToolIds = new Set(
        Array.from(document.querySelectorAll(".run-card .tool-id"))
          .map((input) => String(input.value || "").trim())
          .filter(Boolean)
      );
      for (const tool of listAvailableTools()) {
        if (existingToolIds.has(tool.tool_id)) {
          continue;
        }
        addRunCard({
          tool_id: tool.tool_id,
        });
      }
    } catch (err) {
      pushToast({ title: "Run configuration error", message: err.message, kind: "error", ttlMs: 8000 });
    }
  });
  $("clear-runs-btn").addEventListener("click", () => {
    $("runs-container").innerHTML = "";
    updateRunsEmptyState();
  });
  $("open-tool-request-issue-btn").addEventListener("click", () => {
    try {
      const url = _buildToolRequestIssueUrl();
      window.open(url, "_blank", "noopener");
      pushToast({
        title: "GitHub issue opened",
        message: "Opened prefilled issue in a new tab.",
        kind: "success",
        ttlMs: 4500,
      });
    } catch (err) {
      pushToast({ title: "Tool request error", message: err.message, kind: "error", ttlMs: 7000 });
    }
  });
  $("open-tool-issue-btn").addEventListener("click", () => {
    try {
      const url = _buildToolIssueReportUrl();
      window.open(url, "_blank", "noopener");
      pushToast({
        title: "GitHub issue opened",
        message: "Opened prefilled tool issue in a new tab.",
        kind: "success",
        ttlMs: 4500,
      });
    } catch (err) {
      pushToast({ title: "Tool issue error", message: err.message, kind: "error", ttlMs: 7000 });
    }
  });
  $("analyze-btn").addEventListener("click", () => submitPreflight());
  $("plan-btn").addEventListener("click", () => submitPlan());
  $("execute-btn").addEventListener("click", () => submitRun());
  $("step-1-toggle").addEventListener("click", () => tryOpenStep(1));
  $("step-2-toggle").addEventListener("click", () => tryOpenStep(2));
  $("step-3-toggle").addEventListener("click", () => tryOpenStep(3));
  $("step-1-next-btn").addEventListener("click", () => tryOpenStep(2));
  $("step-2-next-btn").addEventListener("click", () => tryOpenStep(3));
  $("refresh-files-btn").addEventListener("click", async () => {
    if (!state.jobId) {
      pushToast({
        title: "No job selected",
        message: "Submit a job first.",
        kind: "warning",
        ttlMs: 5000,
      });
      return;
    }
    try {
      state.loadedFilesKey = null;
      await fetchFiles(state.jobId);
    } catch (err) {
      pushToast({ title: "Files refresh error", message: err.message, kind: "warning", ttlMs: 7000 });
    }
  });
  $("download-bundle-btn").addEventListener("click", () => {
    if (!state.jobId) {
      pushToast({
        title: "No job selected",
        message: "Submit a job first.",
        kind: "warning",
        ttlMs: 5000,
      });
      return;
    }
    const mode = currentBundleMode();
    const url = `/api/infer-network-v2/jobs/${state.jobId}/bundle?mode=${encodeURIComponent(mode)}`;
    window.open(url, "_blank", "noopener");
  });
  $("bundle-mode").addEventListener("change", async () => {
    state.loadedFilesKey = null;
    state.collapsedDirs.clear();
    if (!state.jobId) {
      resetFilesView("No files loaded yet.");
      return;
    }
    try {
      await fetchFiles(state.jobId);
    } catch (err) {
      pushToast({ title: "Bundle mode error", message: err.message, kind: "warning", ttlMs: 7000 });
    }
  });

  $("info-popover-close").addEventListener("click", () => hideInfoTooltip());
  $("info-popover").addEventListener("click", (event) => {
    if (event.target && event.target.id === "info-popover") {
      hideInfoTooltip();
    }
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      hideInfoTooltip();
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  bindEvents();
  try {
    await bootstrap();
  } catch (err) {
    pushToast({ title: "Initialization error", message: err.message, kind: "error", ttlMs: 9000 });
  }
});
