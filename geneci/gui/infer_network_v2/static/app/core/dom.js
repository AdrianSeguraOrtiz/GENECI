export function $(id) {
  return document.getElementById(id);
}

export function currentBundleMode() {
  const mode = $("bundle-mode")?.value || "full";
  return mode === "light" ? "light" : "full";
}

export function formatBytes(bytes) {
  if (bytes === null || bytes === undefined || Number.isNaN(Number(bytes))) {
    return "-";
  }
  const value = Number(bytes);
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  if (value < 1024 * 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

export function normalizeHelpText(value) {
  const raw = String(value || "");
  if (!raw.includes("\\n") && !raw.includes("\\t") && !raw.includes("\\r")) {
    return raw;
  }
  return raw
    .replace(/\\r\\n/g, "\n")
    .replace(/\\n/g, "\n")
    .replace(/\\t/g, "\t")
    .replace(/\\r/g, "\n");
}

export function normalizeUrlOrDoi(value) {
  const raw = String(value || "").trim();
  if (!raw) {
    return null;
  }
  if (/^https?:\/\//i.test(raw)) {
    return raw;
  }
  if (/^doi\.org\//i.test(raw)) {
    return `https://${raw}`;
  }
  if (/^10\.\S+/i.test(raw)) {
    return `https://doi.org/${raw}`;
  }
  return null;
}

export function appendLinkifiedText(parent, text) {
  const raw = String(text || "");
  const tokenPattern = /(https?:\/\/[^\s|)]+|doi\.org\/[^\s|)]+|10\.\S+)/gi;
  let lastIndex = 0;
  let match = tokenPattern.exec(raw);
  while (match) {
    const token = match[0];
    if (match.index > lastIndex) {
      parent.appendChild(document.createTextNode(raw.slice(lastIndex, match.index)));
    }
    const href = normalizeUrlOrDoi(token);
    if (href) {
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = token;
      parent.appendChild(anchor);
    } else {
      parent.appendChild(document.createTextNode(token));
    }
    lastIndex = match.index + token.length;
    match = tokenPattern.exec(raw);
  }
  if (lastIndex < raw.length) {
    parent.appendChild(document.createTextNode(raw.slice(lastIndex)));
  }
}

export function fillSelect(id, values) {
  const select = $(id);
  if (!select) {
    return;
  }
  select.innerHTML = "";
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }
}
