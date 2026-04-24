import {
  $,
  appendLinkifiedText,
  normalizeHelpText,
  normalizeUrlOrDoi,
} from "../core/dom.js";

export function buildInfoTooltip({ title, description = "", example = "", fields = [] }) {
  return {
    title: String(title || "Info"),
    description: String(description || ""),
    example: String(example || ""),
    fields: Array.isArray(fields) ? fields : [],
  };
}

export function readHelpPayload(node) {
  const raw = String(node?.dataset?.help || "").trim();
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (_err) {
    return null;
  }
}

export function closeInfoTooltip() {
  const popover = $("info-popover");
  const content = $("info-popover-content");
  if (popover) {
    popover.classList.add("hidden");
  }
  if (content) {
    content.innerHTML = "";
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

    const links = Array.isArray(field.links) ? field.links.filter((item) => item && typeof item === "object") : [];
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

export function showInfoTooltip(payload) {
  if (!payload || typeof payload !== "object") {
    return;
  }
  const popover = $("info-popover");
  const content = $("info-popover-content");
  if (!popover || !content) {
    return;
  }
  const titleText = normalizeHelpText(String(payload.title || "Info")).trim();
  const description = normalizeHelpText(String(payload.description || "")).trim();
  const example = normalizeHelpText(String(payload.example || "")).trim();
  const fields = Array.isArray(payload.fields) ? payload.fields : [];
  if (!titleText && !description && !example && !fields.length) {
    return;
  }

  content.innerHTML = "";
  if (titleText) {
    const title = document.createElement("h4");
    title.textContent = titleText;
    content.appendChild(title);
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

export function initInfoPopover() {
  $("info-popover-close")?.addEventListener("click", () => closeInfoTooltip());
  $("info-popover")?.addEventListener("click", (event) => {
    if (event.target && event.target.id === "info-popover") {
      closeInfoTooltip();
    }
  });
}
