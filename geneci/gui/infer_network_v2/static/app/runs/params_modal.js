import { $ } from "../core/dom.js";
import { state } from "../core/state.js";
import { readParamsFromHost, renderParamsHost, resolvedDefaultParams } from "/static-common/app/params/schema_form.js?v=20260423c";

let getToolByIdFn = null;
let renderRunParamsFormFn = null;
let readParamsFromCardFn = null;
let onRunsChangedFn = null;

export function initParamsModal({
  getToolById,
  renderRunParamsForm,
  readParamsFromCard,
  onRunsChanged,
}) {
  getToolByIdFn = getToolById;
  renderRunParamsFormFn = renderRunParamsForm;
  readParamsFromCardFn = readParamsFromCard;
  onRunsChangedFn = onRunsChanged;
}

export function setParamsModalStatus(kind, message) {
  const el = $("params-modal-status");
  if (!el) {
    return;
  }
  el.classList.remove("ok", "err");
  if (kind === "ok") {
    el.classList.add("ok");
  } else if (kind === "err") {
    el.classList.add("err");
  }
  el.textContent = String(message || "").trim();
}

export function closeParamsModal() {
  const modal = $("params-modal");
  if (!modal) {
    return;
  }
  modal.classList.add("hidden");
  state.paramsModalCard = null;
  $("params-modal-title").textContent = "Parameters";
  $("params-modal-form").innerHTML = "";
  setParamsModalStatus("", "Adjust parameters and apply changes.");
}

export function openParamsModal(card) {
  const tool = getToolByIdFn?.(String(card.querySelector(".tool-id")?.value || "").trim());
  if (!tool) {
    throw new Error("Unknown tool");
  }
  let currentParams = resolvedDefaultParams(tool);
  try {
    currentParams = readParamsFromCardFn ? readParamsFromCardFn(card) : resolvedDefaultParams(tool);
  } catch (_err) {
    currentParams = resolvedDefaultParams(tool);
  }
  const modal = $("params-modal");
  const modalTitle = $("params-modal-title");
  const modalForm = $("params-modal-form");
  state.paramsModalCard = card;
  modalTitle.textContent = `${tool.name} · Parameters`;
  setParamsModalStatus("", "Adjust parameters and apply changes.");
  renderParamsHost(modalForm, tool, currentParams, () => {
    try {
      readParamsFromHost(tool, modalForm);
      setParamsModalStatus("", "Adjust parameters and apply changes.");
    } catch (err) {
      setParamsModalStatus("err", String(err?.message || "Invalid parameter value"));
    }
  });
  modal.classList.remove("hidden");
}

export function applyParamsModal() {
  const card = state.paramsModalCard;
  if (!card) {
    closeParamsModal();
    return;
  }
  const tool = getToolByIdFn?.(String(card.querySelector(".tool-id")?.value || "").trim());
  if (!tool) {
    throw new Error("Unknown tool");
  }
  const modalForm = $("params-modal-form");
  const params = readParamsFromHost(tool, modalForm);
  renderRunParamsFormFn(card, tool, params);
  if (typeof onRunsChangedFn === "function") {
    onRunsChangedFn();
  }
  closeParamsModal();
}
