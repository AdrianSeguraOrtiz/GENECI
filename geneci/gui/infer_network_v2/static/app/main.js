import { fetchBootstrapData, submitPlanRequest, submitPreflightRequest, submitRunRequest } from "./core/api.js";
import { $, fillSelect } from "./core/dom.js";
import { state } from "./core/state.js";
import { buildToolIssueReportUrl, buildToolRequestIssueUrl, defaultGroupModeForTool, listAvailableTools, populateToolIssueSelect, toolById } from "./catalog/model.js";
import { initCatalogView, updateToolEligibilityView } from "./catalog/view.js";
import { applyDatasetDefaults, handleExpressionSelected, initExpressionDropzone, syncExpressionHelpTooltip } from "./dataset/expression.js";
import { addOptionalExtraRow, getExtraRows, initExtras, listProvidedExtraKeys, updateExtrasEmptyState } from "./dataset/extras.js";
import { renderRuntimeProgress, renderExecutionAlerts } from "./runtime/view.js";
import { fetchFiles, resetFilesView } from "./files/explorer.js";
import { freezeActions, startPolling, syncActionButtons, updateResultsExplorerVisibility } from "./jobs/controller.js";
import { resetPlanView } from "./plan/view.js";
import { closeReproducibilityStepsModal, initReproducibility, resetReproducibility } from "./repro/view.js";
import { closeParamsModal, initParamsModal, openParamsModal, applyParamsModal, setParamsModalStatus } from "./runs/params_modal.js";
import { addRunCard, collectRuns, initRunCards, readParamsFromCard, refreshRunCardsValidation, renderRunParamsForm, updateRunsEmptyState } from "./runs/cards.js";
import { readParamsFromHost, renderParamsHost, resolvedDefaultParams } from "./runs/schema_form.js";
import { buildInfoTooltip, hideInfoTooltip, readHelpPayload, showInfoTooltip } from "./ui/popovers.js";
import { setActiveStep, setStepState } from "./ui/steps.js";
import { pushToast } from "./ui/toasts.js";

function buildDatasetConfig() {
  const datasetId = $("dataset-id").value.trim();
  if (!datasetId) {
    throw new Error("dataset_id is required.");
  }
  const organismTaxIdRaw = $("organism-tax-id").value.trim();
  const organismTaxId = Number(organismTaxIdRaw);
  if (!organismTaxIdRaw || !Number.isInteger(organismTaxId) || organismTaxId < 1) {
    throw new Error("organism.tax_id must be a positive integer.");
  }

  return {
    dataset: {
      id: datasetId,
      column_kind: $("column-kind").value,
      expression_profile: $("expression-profile").value,
      organism: {
        tax_id: organismTaxId,
      },
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
    state.loadedFilesKey = null;
    state.selectedFilePath = null;
    state.collapsedDirs.clear();
    state.eligibleToolIds = null;
    state.preflightReport = null;
    state.lastPlan = null;
    state.runtimeProgress = null;
    state.currentJob = null;
    state.notifiedFailures.clear();
    state.notifiedJobError = "";
    setActiveStep(1, { scroll: false });
    $("runs-container").innerHTML = "";
    updateRunsEmptyState();
    updateToolEligibilityView(null);
    resetPlanView("Waiting for preflight/plan output...");
    updateResultsExplorerVisibility(null);
    resetReproducibility();
    renderRuntimeProgress(null);
    renderExecutionAlerts(null, null);

    const payload = await submitPreflightRequest(formData);
    state.jobId = payload.job_id;
    state.currentJob = {
      job_id: payload.job_id,
      stage: "draft",
      status: "queued",
    };
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

    const payload = await submitPlanRequest({
      job_id: state.jobId,
      runs,
      options: buildOptions(),
    });
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

    const payload = await submitRunRequest({
      job_id: state.jobId,
      options: {
        progress_poll_seconds: Number($("progress-poll").value),
        strict: $("strict").checked,
      },
    });
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
  state.bootstrap = await fetchBootstrapData();
  fillSelect("column-kind", state.bootstrap.column_kinds);
  fillSelect("expression-profile", state.bootstrap.expression_profiles);
  applyDatasetDefaults();
  populateToolIssueSelect();
  syncExpressionHelpTooltip();
  const strictInfoBtn = $("strict-info-btn");
  if (strictInfoBtn) {
    strictInfoBtn.dataset.help = JSON.stringify(
      buildInfoTooltip({
        title: "Strict Mode",
        description:
          "Fail fast on incompatibilities and execution failures. Without strict mode, incompatible tools may be skipped during analysis and successful tools can still complete even if others fail.",
        example: "",
      })
    );
  }
  initExpressionDropzone();
  await handleExpressionSelected(null);
  updateExtrasEmptyState();
  updateRunsEmptyState();
  updateToolEligibilityView(null);
  resetPlanView("No plan loaded yet.");
  updateResultsExplorerVisibility(null);
  resetReproducibility();
  renderRuntimeProgress(null);
  renderExecutionAlerts(null, null);
  state.notifiedFailures.clear();
  state.notifiedJobError = "";
  state.currentJob = null;
  setActiveStep(1, { scroll: false });
  syncActionButtons();
}

function bindEvents() {
  const openModal = (id) => $(id)?.classList.remove("hidden");
  const closeModal = (id) => $(id)?.classList.add("hidden");

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
  $("strict-info-btn").addEventListener("click", () => {
    const payload = readHelpPayload($("strict-info-btn"));
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
    refreshRunCardsValidation();
    syncActionButtons();
  });
  $("open-tool-request-modal-btn").addEventListener("click", () => openModal("tool-request-modal"));
  $("open-tool-issue-modal-btn").addEventListener("click", () => openModal("tool-issue-modal"));
  $("tool-request-modal-close").addEventListener("click", () => closeModal("tool-request-modal"));
  $("tool-issue-modal-close").addEventListener("click", () => closeModal("tool-issue-modal"));
  $("tool-request-modal").addEventListener("click", (event) => {
    if (event.target && event.target.id === "tool-request-modal") {
      closeModal("tool-request-modal");
    }
  });
  $("tool-issue-modal").addEventListener("click", (event) => {
    if (event.target && event.target.id === "tool-issue-modal") {
      closeModal("tool-issue-modal");
    }
  });
  $("open-tool-request-issue-btn").addEventListener("click", () => {
    try {
      const url = buildToolRequestIssueUrl();
      window.open(url, "_blank", "noopener");
      closeModal("tool-request-modal");
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
      const url = buildToolIssueReportUrl();
      window.open(url, "_blank", "noopener");
      closeModal("tool-issue-modal");
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
    const mode = String($("bundle-mode")?.value || "full");
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
  $("params-modal-close").addEventListener("click", () => closeParamsModal());
  $("params-modal").addEventListener("click", (event) => {
    if (event.target && event.target.id === "params-modal") {
      closeParamsModal();
    }
  });
  $("params-modal-reset").addEventListener("click", () => {
    const card = state.paramsModalCard;
    if (!card) {
      return;
    }
    const tool = toolById(String(card.querySelector(".tool-id")?.value || "").trim());
    if (!tool) {
      return;
    }
    renderParamsHost($("params-modal-form"), tool, resolvedDefaultParams(tool), () => {
      try {
        readParamsFromHost(tool, $("params-modal-form"));
        setParamsModalStatus("", "Adjust parameters and apply changes.");
      } catch (err) {
        setParamsModalStatus("err", String(err?.message || "Invalid parameter value"));
      }
    });
    setParamsModalStatus("", "Tool defaults restored in the editor.");
  });
  $("params-modal-save").addEventListener("click", () => {
    try {
      applyParamsModal();
    } catch (err) {
      setParamsModalStatus("err", String(err?.message || "Invalid parameter value"));
    }
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      hideInfoTooltip();
      closeParamsModal();
      closeModal("tool-request-modal");
      closeModal("tool-issue-modal");
      closeReproducibilityStepsModal();
    }
  });
}

function initModules() {
  initExtras({
    onDatasetChanged: () => {
      refreshRunCardsValidation();
      syncActionButtons();
    },
  });
  initParamsModal({
    getToolById: toolById,
    renderRunParamsForm,
    readParamsFromCard,
    onRunsChanged: () => {
      refreshRunCardsValidation();
      syncActionButtons();
    },
  });
  initRunCards({
    getToolById: toolById,
    listAvailableTools,
    listProvidedExtraKeys,
    defaultGroupModeForTool,
    openParamsModal: (card) => {
      try {
        openParamsModal(card);
      } catch (err) {
        pushToast({ title: "Parameters error", message: err.message, kind: "error", ttlMs: 7000 });
      }
    },
    onRunsChanged: () => {
      syncActionButtons();
    },
  });
  initCatalogView({
    onAddRun: addRunCard,
  });
  initReproducibility();
}

window.addEventListener("DOMContentLoaded", async () => {
  initModules();
  bindEvents();
  try {
    await bootstrap();
  } catch (err) {
    pushToast({ title: "Initialization error", message: err.message, kind: "error", ttlMs: 9000 });
  }
});
