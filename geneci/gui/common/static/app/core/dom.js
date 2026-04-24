export function $(id) {
  return document.getElementById(id);
}

export function formatBytes(value) {
  if (value === null || value === undefined) {
    return "";
  }
  const size = Number(value);
  if (!Number.isFinite(size)) {
    return "";
  }
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function currentBundleMode(id = "bundle-mode") {
  const node = $(id);
  return String(node?.value || "full");
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
