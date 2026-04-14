import { $ } from "../core/dom.js";
import { state } from "../core/state.js";
import { pushToast } from "../ui/toasts.js";

export function renderRuntimeProgress(runtimeProgress = null) {
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

export function pushRuntimeFailureToasts(runtimeProgress = null) {
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

function normalizeExecutionAlertMessage(message) {
  let normalized = String(message || "").trim();
  normalized = normalized.replace(/^\[([^\]]+)\]\s+execution failed:\s*/i, "");
  normalized = normalized.replace(/^[A-Za-z0-9_]+:\s*/i, "");
  return normalized.trim();
}

function isPreExecutionWarning(message) {
  const text = String(message || "").trim().toLowerCase();
  return text.includes("optional extra not provided");
}

export function renderExecutionAlerts(job = null, runReport = null) {
  const root = $("execution-alerts");
  if (!root) {
    return;
  }
  root.innerHTML = "";

  const errors = [];
  const executionWarnings = [];
  const preExecutionWarnings = [];
  const rawWarnings = runReport && Array.isArray(runReport.warnings)
    ? runReport.warnings.map((x) => String(x)).filter(Boolean)
    : [];
  const errorSignatures = new Set();

  const failedMap = runReport?.tools?.failed;
  if (failedMap && typeof failedMap === "object") {
    for (const [runId, reason] of Object.entries(failedMap)) {
      const message = `${runId}: ${String(reason || "failed")}`;
      errors.push(message);
      errorSignatures.add(normalizeExecutionAlertMessage(message));
    }
  }

  const jobError = String(job?.error || "").trim();
  if (jobError) {
    errors.push(jobError);
    errorSignatures.add(normalizeExecutionAlertMessage(jobError));
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

  const warningSeen = new Set();
  for (const message of rawWarnings) {
    const signature = normalizeExecutionAlertMessage(message);
    if (errorSignatures.has(signature)) {
      continue;
    }
    const bucket = isPreExecutionWarning(message) ? "pre" : "exec";
    const dedupeKey = `${bucket}:${signature}`;
    if (warningSeen.has(dedupeKey)) {
      continue;
    }
    warningSeen.add(dedupeKey);
    if (bucket === "pre") {
      preExecutionWarnings.push(message);
    } else {
      executionWarnings.push(message);
    }
  }

  if (!errors.length && !executionWarnings.length && !preExecutionWarnings.length) {
    root.textContent = "No execution errors or warnings.";
    return;
  }

  const title = document.createElement("div");
  title.className = "execution-alerts-title";
  title.textContent =
    `Execution alerts: ${errors.length} error(s), ` +
    `${executionWarnings.length} execution warning(s), ` +
    `${preExecutionWarnings.length} pre-execution note(s)`;
  root.appendChild(title);

  const renderAlertSection = (sectionTitle, messages, className) => {
    if (!messages.length) {
      return;
    }
    const section = document.createElement("section");
    section.className = "execution-alerts-section";
    const heading = document.createElement("div");
    heading.className = "execution-alerts-section-title";
    heading.textContent = sectionTitle;
    section.appendChild(heading);
    for (const message of messages.slice(0, 8)) {
      const line = document.createElement("div");
      line.className = `execution-alert ${className}`;
      line.textContent = message;
      section.appendChild(line);
    }
    root.appendChild(section);
  };

  renderAlertSection("Execution errors", errors, "error");
  renderAlertSection("Execution warnings", executionWarnings, "warning");
  renderAlertSection("Pre-execution notes", preExecutionWarnings, "warning");

  const hiddenErrors = Math.max(0, errors.length - 8);
  const hiddenExecutionWarnings = Math.max(0, executionWarnings.length - 8);
  const hiddenPreExecutionWarnings = Math.max(0, preExecutionWarnings.length - 8);
  if (hiddenErrors || hiddenExecutionWarnings || hiddenPreExecutionWarnings) {
    const parts = [];
    if (hiddenErrors) {
      parts.push(`${hiddenErrors} more error(s)`);
    }
    if (hiddenExecutionWarnings) {
      parts.push(`${hiddenExecutionWarnings} more execution warning(s)`);
    }
    if (hiddenPreExecutionWarnings) {
      parts.push(`${hiddenPreExecutionWarnings} more pre-execution note(s)`);
    }
    const more = document.createElement("div");
    more.className = "execution-alert";
    more.textContent = `... and ${parts.join(", ")}`;
    root.appendChild(more);
  }
}
