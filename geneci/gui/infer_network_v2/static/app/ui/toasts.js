import { $ } from "../core/dom.js";

export function pushToast({ title, message, kind = "error", ttlMs = 7000 }) {
  const host = $("toast-container");
  if (!host) {
    return;
  }
  const toast = document.createElement("article");
  toast.className = `toast ${kind}`;

  const textWrap = document.createElement("div");
  const titleNode = document.createElement("p");
  titleNode.className = "toast-title";
  titleNode.textContent = String(title || "Notice");
  const bodyNode = document.createElement("p");
  bodyNode.className = "toast-body";
  bodyNode.textContent = String(message || "").trim() || "-";
  textWrap.appendChild(titleNode);
  textWrap.appendChild(bodyNode);

  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "toast-close";
  closeBtn.textContent = "×";
  closeBtn.setAttribute("aria-label", "Close notification");
  closeBtn.addEventListener("click", () => toast.remove());

  toast.appendChild(textWrap);
  toast.appendChild(closeBtn);
  host.appendChild(toast);

  if (ttlMs > 0) {
    window.setTimeout(() => {
      toast.remove();
    }, ttlMs);
  }
}
