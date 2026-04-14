import { $ } from "../core/dom.js";
import { state } from "../core/state.js";

export function resetPlanView(message) {
  state.lastPlan = null;
  $("plan-summary").textContent = message || "No plan loaded yet.";
  $("plan-waves").innerHTML = "";
}

export function renderPlan(plan) {
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
    `logical_runs_total: ${totals.logical_runs_total ?? "-"}`,
    `physical_tasks_total: ${totals.physical_tasks_total ?? totals.tasks_total ?? "-"}`,
    `waves_total: ${totals.waves_total ?? "-"}`,
    `threads_peak: ${totals.threads_peak ?? "-"}`,
    `ram_peak_gb: ${totals.ram_peak_gb ?? "-"}`,
    `eta_total_seconds: ${plan.eta_total_seconds ?? "-"}`,
  ];
  $("plan-summary").textContent = lines.join("\n");

  const wavesRoot = $("plan-waves");
  wavesRoot.innerHTML = "";
  const logicalRuns = Array.isArray(plan.runs) ? plan.runs : [];
  const waves = Array.isArray(plan.waves) ? plan.waves : [];
  if (!logicalRuns.length && !waves.length) {
    wavesRoot.textContent = "This plan has no waves.";
    return;
  }

  if (logicalRuns.length) {
    const runsCard = document.createElement("article");
    runsCard.className = "wave-card";

    const runsHead = document.createElement("div");
    runsHead.className = "wave-head";
    runsHead.innerHTML =
      `<span class="wave-title">Configured Runs</span>` +
      `<span>runs=${logicalRuns.length}</span>`;
    runsCard.appendChild(runsHead);

    const runsTable = document.createElement("table");
    runsTable.className = "wave-table";
    runsTable.innerHTML =
      "<thead><tr>" +
      "<th>run_id</th><th>tool_id</th><th>mode</th><th>scope</th><th>physical_tasks</th><th>eta_s</th>" +
      "</tr></thead>";
    const runsBody = document.createElement("tbody");
    for (const run of logicalRuns) {
      const tr = document.createElement("tr");
      const cells = [
        run.run_id || "-",
        run.tool_id || "-",
        run?.execution?.group_mode || "-",
        run.execution_scope || "-",
        run.physical_tasks_total ?? "-",
        run.eta_seconds ?? "-",
      ];
      for (const value of cells) {
        const td = document.createElement("td");
        td.textContent = String(value);
        tr.appendChild(td);
      }
      runsBody.appendChild(tr);
    }
    runsTable.appendChild(runsBody);
    runsCard.appendChild(runsTable);
    wavesRoot.appendChild(runsCard);
  }

  if (!waves.length) {
    return;
  }

  const wavesDetails = document.createElement("details");
  wavesDetails.className = "muted-box";
  if (!logicalRuns.length) {
    wavesDetails.open = true;
  }
  const wavesSummary = document.createElement("summary");
  wavesSummary.textContent = `Internal waves (${waves.length})`;
  wavesDetails.appendChild(wavesSummary);

  const wavesHost = document.createElement("div");
  wavesHost.className = "plan-waves";

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
      "<th>run_id</th><th>task_id</th><th>group</th><th>threads</th><th>ram_gb</th><th>eta_s</th><th>source</th><th>note</th>" +
      "</tr></thead>";

    const tbody = document.createElement("tbody");
    const tasks = Array.isArray(wave.tasks) ? wave.tasks : [];
    for (const task of tasks) {
      const tr = document.createElement("tr");
      const cells = [
        task.run_id || task.tool_id || "-",
        task.tool_id || "-",
        task.group_label || "-",
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
    wavesHost.appendChild(card);
  }
  wavesDetails.appendChild(wavesHost);
  wavesRoot.appendChild(wavesDetails);
}

export function renderPlanInlinePreview(plan, virtualPath) {
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
  const logicalRuns = Array.isArray(plan.runs) ? plan.runs : [];
  const waves = Array.isArray(plan.waves) ? plan.waves : [];
  if (logicalRuns.length) {
    const runsCard = document.createElement("article");
    runsCard.className = "wave-card";
    const runsHead = document.createElement("div");
    runsHead.className = "wave-head";
    runsHead.innerHTML = `<span class="wave-title">Configured Runs</span><span>runs=${logicalRuns.length}</span>`;
    runsCard.appendChild(runsHead);
    const runsTable = document.createElement("table");
    runsTable.className = "wave-table";
    runsTable.innerHTML =
      "<thead><tr>" +
      "<th>run_id</th><th>tool_id</th><th>mode</th><th>scope</th><th>physical_tasks</th><th>eta_s</th>" +
      "</tr></thead>";
    const runsBody = document.createElement("tbody");
    for (const run of logicalRuns) {
      const tr = document.createElement("tr");
      const cells = [
        run.run_id || "-",
        run.tool_id || "-",
        run?.execution?.group_mode || "-",
        run.execution_scope || "-",
        run.physical_tasks_total ?? "-",
        run.eta_seconds ?? "-",
      ];
      for (const value of cells) {
        const td = document.createElement("td");
        td.textContent = String(value);
        tr.appendChild(td);
      }
      runsBody.appendChild(tr);
    }
    runsTable.appendChild(runsBody);
    runsCard.appendChild(runsTable);
    wavesHost.appendChild(runsCard);
  }
  if (!waves.length) {
    if (logicalRuns.length) {
      previewRoot.appendChild(wavesHost);
      return;
    }
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
    head.innerHTML = `<span class="wave-title">Wave ${wave.index}</span><span>tasks=${Array.isArray(
      wave.tasks
    ) ? wave.tasks.length : 0}</span><span>cores=${wave.threads_used ?? "-"}</span><span>ram=${
      wave.ram_gb_used ?? "-"
    }GB</span>`;
    card.appendChild(head);
    const table = document.createElement("table");
    table.className = "wave-table";
    table.innerHTML =
      "<thead><tr>" +
      "<th>run_id</th><th>task_id</th><th>group</th><th>threads</th><th>ram_gb</th><th>eta_s</th><th>source</th><th>note</th>" +
      "</tr></thead>";
    const tbody = document.createElement("tbody");
    const tasks = Array.isArray(wave.tasks) ? wave.tasks : [];
    for (const task of tasks) {
      const tr = document.createElement("tr");
      const cells = [
        task.run_id || task.tool_id || "-",
        task.tool_id || "-",
        task.group_label || "-",
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
