import { $ } from "../core/dom.js";
import { pushToast } from "../ui/toasts.js";

export function renderRuntimeProgress(runtimeProgress = null, rootId = "runtime-progress") {
  const root = $(rootId);
  if (!root) {
    return;
  }
  const items = Array.isArray(runtimeProgress?.tasks)
    ? runtimeProgress.tasks
    : Array.isArray(runtimeProgress?.tools)
      ? runtimeProgress.tools
      : [];
  if (!items.length) {
    root.textContent = "No runtime progress yet.";
    return;
  }
  root.innerHTML = "";
  const summary = runtimeProgress.summary || {};
  const header = document.createElement("div");
  header.className = "preflight-list-line";
  header.textContent =
    `total=${summary.total ?? items.length} | running=${summary.running ?? 0} | ` +
    `completed=${summary.completed ?? 0} | failed=${summary.failed ?? 0}`;
  root.appendChild(header);

  const sorted = [...items].sort((a, b) =>
    String(a.task_id || a.run_id || "").localeCompare(String(b.task_id || b.run_id || ""))
  );
  for (const item of sorted) {
    const row = document.createElement("article");
    row.className = "runtime-progress-row";

    const head = document.createElement("div");
    head.className = "runtime-progress-head";
    const left = document.createElement("span");
    left.textContent =
      `${item.task_id || item.run_id || "-"} · ${item.status || "unknown"} · ${item.phase || "-"}`;
    const right = document.createElement("span");
    right.textContent = `${Number(item.percent || 0)}%`;
    head.appendChild(left);
    head.appendChild(right);
    row.appendChild(head);

    const bar = document.createElement("div");
    bar.className = "runtime-progress-bar";
    const fill = document.createElement("div");
    fill.className = "runtime-progress-fill";
    fill.classList.add(`status-${String(item.status || "pending").toLowerCase()}`);
    fill.style.width = `${Math.max(0, Math.min(100, Number(item.percent || 0)))}%`;
    bar.appendChild(fill);
    row.appendChild(bar);

    const msg = document.createElement("div");
    msg.className = "preflight-list-line";
    msg.textContent = String(item.message || "").trim() || "No message";
    row.appendChild(msg);
    root.appendChild(row);
  }
}

export function pushRuntimeFailureToasts(runtimeProgress = null, notifiedFailures = new Set()) {
  const items = Array.isArray(runtimeProgress?.tasks)
    ? runtimeProgress.tasks
    : Array.isArray(runtimeProgress?.tools)
      ? runtimeProgress.tools
      : [];
  for (const item of items) {
    const id = String(item?.task_id || item?.run_id || "").trim();
    const status = String(item?.status || "").trim().toLowerCase();
    if (!id || status !== "failed" || notifiedFailures.has(id)) {
      continue;
    }
    notifiedFailures.add(id);
    pushToast({
      title: `Task failed: ${id}`,
      message: String(item?.message || "").trim() || "Execution failed.",
      kind: "error",
      ttlMs: 9000,
    });
  }
}

