import { $ } from "../core/dom.js";
import { state } from "../core/state.js";
import { pushToast } from "../ui/toasts.js";
import { showInfoTooltip } from "../ui/popovers.js";
import { updatePreflightSummary } from "../preflight/view.js";
import { toolById, toolMessages, toolSpecInfoPayload } from "./model.js";

let onAddRunFn = null;

export function initCatalogView({ onAddRun }) {
  onAddRunFn = onAddRun;
}

function renderToolCatalogList(containerId, entries, kind) {
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
      showInfoTooltip(toolSpecInfoPayload(tool));
    });

    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "Add Run";
    addBtn.className = "secondary";
    addBtn.addEventListener("click", () => {
      try {
        if (typeof onAddRunFn === "function") {
          onAddRunFn({ tool_id: tool.tool_id });
        }
      } catch (err) {
        pushToast({ title: "Run configuration error", message: err.message, kind: "error", ttlMs: 8000 });
      }
    });

    const infoBtn = document.createElement("button");
    infoBtn.type = "button";
    infoBtn.textContent = kind === "blocked" ? "Why Blocked" : "View Details";
    const messages = toolMessages(entry);
    infoBtn.addEventListener("click", () => {
      const detailLines =
        kind === "blocked" && toolId
          ? messages.map((message) =>
              String(message || "").startsWith(`[${toolId}]`)
                ? String(message)
                : `[${toolId}] ${String(message)}`
            )
          : messages;
      showInfoTooltip({
        title: tool.name,
        description: detailLines.length ? detailLines.join("\n") : "No additional details.",
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

export function updateToolEligibilityView(preflightReport = null) {
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

  renderToolCatalogList("tools-eligible-list", eligible, "eligible");
  renderToolCatalogList("tools-warning-list", warning, "warning");
  renderToolCatalogList("tools-blocked-list", blocked, "blocked");
}
