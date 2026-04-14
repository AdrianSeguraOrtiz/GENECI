import { $, formatBytes } from "../core/dom.js";
import { pushToast } from "../ui/toasts.js";
import { buildInfoTooltip, readHelpPayload, showInfoTooltip } from "../ui/popovers.js";
import { state } from "../core/state.js";
import { getExtraMeta, setStatusBadge, validateOptionalFile } from "./validation.js";

let onDatasetChangedFn = null;

export function initExtras({ onDatasetChanged }) {
  onDatasetChangedFn = onDatasetChanged;
}

function notifyDatasetChanged() {
  if (typeof onDatasetChangedFn === "function") {
    onDatasetChangedFn();
  }
}

export function getExtraRows() {
  return Array.from(document.querySelectorAll(".extra-row"));
}

export function updateExtrasEmptyState() {
  const hasExtras = getExtraRows().length > 0;
  $("extras-empty").style.display = hasExtras ? "none" : "block";
}

export function listExtraKeys() {
  return Array.isArray(state.bootstrap?.extra_inputs) ? state.bootstrap.extra_inputs.map((item) => item.key) : [];
}

export function listProvidedExtraKeys() {
  return new Set(
    getExtraRows()
      .map((row) => {
        const key = String(row.querySelector(".extra-key")?.value || "").trim();
        const file = row.querySelector(".extra-file")?.files?.[0] || null;
        return key && file ? key : "";
      })
      .filter(Boolean)
  );
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
    notifyDatasetChanged();
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
  notifyDatasetChanged();
}

export function refreshExtraSelectOptions() {
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

export function addOptionalExtraRow(preferredKey = null) {
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
    notifyDatasetChanged();
  });

  $("extras-list").appendChild(node);
  updateExtrasEmptyState();
  refreshExtraSelectOptions();
  syncExtraRowMeta(node);
  notifyDatasetChanged();
}
