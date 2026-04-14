import { $ } from "../core/dom.js";
import { pushToast } from "../ui/toasts.js";

function copyCode(text) {
  if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
    pushToast({
      title: "Copy not available",
      message: "Clipboard access is not available in this browser context.",
      kind: "warning",
      ttlMs: 5000,
    });
    return;
  }
  navigator.clipboard
    .writeText(String(text || ""))
    .then(() => {
      pushToast({
        title: "Copied",
        message: "Snippet copied to clipboard.",
        kind: "success",
        ttlMs: 2500,
      });
    })
    .catch((err) => {
      pushToast({
        title: "Copy failed",
        message: String(err?.message || "Clipboard write failed."),
        kind: "warning",
        ttlMs: 5000,
      });
    });
}

function buildCodeBlock({ label, language, code }) {
  const wrap = document.createElement("section");
  wrap.className = "repro-code-block";

  const head = document.createElement("div");
  head.className = "repro-code-head";
  const title = document.createElement("strong");
  title.textContent = label;
  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "secondary";
  copyBtn.textContent = "Copy";
  copyBtn.addEventListener("click", () => copyCode(code));
  head.appendChild(title);
  head.appendChild(copyBtn);

  const codeWrap = document.createElement("div");
  codeWrap.className = "repro-code-wrap";
  const lang = document.createElement("div");
  lang.className = "repro-code-lang";
  lang.textContent = language;
  const pre = document.createElement("pre");
  pre.textContent = String(code || "").trim();
  codeWrap.appendChild(lang);
  codeWrap.appendChild(pre);

  wrap.appendChild(head);
  wrap.appendChild(codeWrap);
  return wrap;
}

function buildCard(card) {
  const article = document.createElement("article");
  article.className = "repro-card";

  const head = document.createElement("div");
  head.className = "repro-card-head";
  const title = document.createElement("h4");
  title.textContent = String(card?.title || "Snippet");
  head.appendChild(title);
  article.appendChild(head);

  const summary = document.createElement("p");
  summary.className = "repro-summary";
  summary.textContent = String(card?.summary || "").trim();
  article.appendChild(summary);

  const note = String(card?.note || "").trim();
  if (note) {
    const noteEl = document.createElement("div");
    noteEl.className = "muted-box repro-note";
    noteEl.textContent = note;
    article.appendChild(noteEl);
  }

  article.appendChild(
    buildCodeBlock({
      label: String(card?.primary_label || "Snippet"),
      language: String(card?.primary_language || "text"),
      code: String(card?.primary_code || ""),
    })
  );

  const steps = Array.isArray(card?.steps) ? card.steps : [];
  if (steps.length) {
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "secondary repro-steps-trigger";
    trigger.textContent = String(card?.steps_label || "By steps");
    trigger.addEventListener("click", () => openReproStepsModal(card));
    article.appendChild(trigger);
  }

  return article;
}

export function closeReproducibilityStepsModal() {
  const modal = $("repro-steps-modal");
  const body = $("repro-steps-modal-body");
  const title = $("repro-steps-modal-title");
  if (modal) {
    modal.classList.add("hidden");
  }
  if (body) {
    body.innerHTML = "";
  }
  if (title) {
    title.textContent = "Reproducibility Steps";
  }
}

function openReproStepsModal(card) {
  const modal = $("repro-steps-modal");
  const body = $("repro-steps-modal-body");
  const title = $("repro-steps-modal-title");
  if (!modal || !body || !title) {
    return;
  }
  body.innerHTML = "";
  title.textContent = `${String(card?.title || "Snippet")} · By steps`;
  const steps = Array.isArray(card?.steps) ? card.steps : [];
  for (const step of steps) {
    body.appendChild(
      buildCodeBlock({
        label: String(step?.title || "Step"),
        language: String(step?.language || "text"),
        code: String(step?.code || ""),
      })
    );
  }
  modal.classList.remove("hidden");
}

export function initReproducibility() {
  $("repro-steps-modal-close")?.addEventListener("click", () => closeReproducibilityStepsModal());
  $("repro-steps-modal")?.addEventListener("click", (event) => {
    if (event.target && event.target.id === "repro-steps-modal") {
      closeReproducibilityStepsModal();
    }
  });
}

export function resetReproducibility(message = "Reproducibility snippets will be available after execution.") {
  const section = $("reproducibility-section");
  const placeholder = $("reproducibility-placeholder");
  const grid = $("reproducibility-grid");
  if (section) {
    section.hidden = true;
  }
  if (grid) {
    grid.innerHTML = "";
  }
  if (placeholder) {
    placeholder.hidden = false;
    placeholder.textContent = message;
  }
  closeReproducibilityStepsModal();
}

export function renderReproducibility(payload = null) {
  const section = $("reproducibility-section");
  const placeholder = $("reproducibility-placeholder");
  const grid = $("reproducibility-grid");
  if (!section || !placeholder || !grid) {
    return;
  }

  if (!payload || !payload.available) {
    resetReproducibility(String(payload?.message || "").trim() || undefined);
    return;
  }

  section.hidden = false;
  placeholder.hidden = true;
  grid.innerHTML = "";

  for (const key of ["cli", "python"]) {
    if (!payload[key] || typeof payload[key] !== "object") {
      continue;
    }
    grid.appendChild(buildCard(payload[key]));
  }
}
