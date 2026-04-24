import { $ } from "../core/dom.js";

export function setStepState(step, state) {
  const node = $(`step-${step}-state`);
  if (!node) {
    return;
  }
  node.classList.remove("draft", "ready", "blocked", "running");
  if (state) {
    node.classList.add(String(state));
    node.textContent = String(state);
  }
}

export function setActiveStep(step, { scroll = true } = {}) {
  document.querySelectorAll(".workflow-step").forEach((node) => {
    node.classList.toggle("is-active", String(node.dataset.step) === String(step));
  });
  if (scroll) {
    $(`step-${step}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

export function initSteps(maxStep = 3) {
  for (let idx = 1; idx <= maxStep; idx += 1) {
    $(`step-${idx}-toggle`)?.addEventListener("click", () => setActiveStep(idx));
  }
}
