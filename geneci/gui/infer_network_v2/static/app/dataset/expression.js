import { $, formatBytes } from "../core/dom.js";
import { buildInfoTooltip } from "../ui/popovers.js";
import { getExpressionHelp, setStatusBadge, validateExpressionFile } from "./validation.js";

export function syncExpressionHelpTooltip() {
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

export function syncExpressionFileLabel() {
  const input = $("expression-file");
  const label = $("expression-file-name");
  if (!input || !label) {
    return;
  }
  const file = input.files && input.files[0] ? input.files[0] : null;
  label.textContent = file ? `${file.name} (${formatBytes(file.size)})` : "No file selected";
}

export async function handleExpressionSelected(file) {
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
      `Valid: ${inspected.genes} gene rows x ${inspected.columns} columns`
    );
  } catch (err) {
    setStatusBadge(statusEl, "err", `Invalid expression matrix: ${err.message}`);
  }
}

export function setInputFile(input, file) {
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
}

export function initExpressionDropzone() {
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

export function applyDatasetDefaults() {
  const columnKind = $("column-kind");
  const expressionProfile = $("expression-profile");
  if (!columnKind || !expressionProfile) {
    return;
  }
  const columnKindValues = Array.from(columnKind.options).map((option) => option.value);
  const expressionProfileValues = Array.from(expressionProfile.options).map((option) => option.value);

  if (columnKindValues.includes("cells")) {
    columnKind.value = "cells";
  }
  if (columnKind.value === "cells" && expressionProfileValues.includes("scrna")) {
    expressionProfile.value = "scrna";
  } else if (expressionProfileValues.includes("bulk")) {
    expressionProfile.value = "bulk";
  }
}
