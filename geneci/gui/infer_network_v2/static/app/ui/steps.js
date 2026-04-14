import { $ } from "../core/dom.js";
import { state } from "../core/state.js";

export function setActiveStep(stepNumber, options = {}) {
  const { scroll = true } = options;
  const step = Number(stepNumber);
  if (!Number.isFinite(step) || step < 1 || step > 3) {
    return;
  }
  state.activeStep = step;
  for (const item of document.querySelectorAll(".workflow-step")) {
    const value = Number(item.dataset.step || "0");
    item.classList.toggle("is-active", value === step);
  }
  if (scroll) {
    const panel = $(`step-${step}`);
    if (panel && typeof panel.scrollIntoView === "function") {
      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.requestAnimationFrame(() => {
        panel.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
      });
    }
  }
}

export function setStepState(stepNumber, value) {
  const badge = $(`step-${stepNumber}-state`);
  if (!badge) {
    return;
  }
  badge.classList.remove("ready", "blocked", "running");
  const normalized = String(value || "blocked");
  if (normalized === "ready") {
    badge.classList.add("ready");
  } else if (normalized === "running") {
    badge.classList.add("running");
  } else {
    badge.classList.add("blocked");
  }
  badge.textContent = normalized;
}
