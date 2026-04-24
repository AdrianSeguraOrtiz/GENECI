import { $, currentBundleMode, formatBytes } from "../core/dom.js";
import { pushToast } from "../ui/toasts.js";

const DEFAULT_IDS = {
  summary: "files-summary",
  tree: "files-tree",
  header: "file-preview-header",
  preview: "file-preview",
  bundleMode: "bundle-mode",
};

function targetId(ids, key) {
  return ids?.[key] || DEFAULT_IDS[key];
}

function target(ids, key) {
  return $(targetId(ids, key));
}

function ensureFileState(state) {
  if (!state.collapsedDirs || !(state.collapsedDirs instanceof Set)) {
    state.collapsedDirs = new Set();
  }
  if (!Array.isArray(state.filesEntries)) {
    state.filesEntries = [];
  }
}

function viewerLabel(viewer) {
  const raw = String(viewer || "none");
  if (raw === "network_gexf") {
    return "gexf";
  }
  if (raw === "network_graphml") {
    return "graphml";
  }
  if (raw === "network_cytoscape_script") {
    return "cytoscape";
  }
  if (raw === "table_csv") {
    return "csv";
  }
  if (raw === "table_tsv") {
    return "tsv";
  }
  return raw;
}

export function resetFilesView(state, message, ids = {}) {
  ensureFileState(state);
  state.selectedFilePath = null;
  state.filesEntries = [];
  state.filesMode = currentBundleMode(targetId(ids, "bundleMode"));
  target(ids, "summary").textContent = message || "No files loaded yet.";
  target(ids, "tree").innerHTML = "";
  target(ids, "header").textContent = "Select a file to preview.";
  target(ids, "preview").innerHTML = "";
}

function appendGuide(card, guide) {
  const title = document.createElement("h4");
  title.textContent = String(guide.title || "Artifact guide");
  card.appendChild(title);

  const summary = document.createElement("p");
  summary.textContent = String(guide.summary || "");
  card.appendChild(summary);

  const tips = Array.isArray(guide.tips) ? guide.tips : [];
  if (tips.length) {
    const list = document.createElement("ul");
    list.className = "network-export-tips";
    for (const tip of tips) {
      const li = document.createElement("li");
      li.textContent = String(tip);
      list.appendChild(li);
    }
    card.appendChild(list);
  }

  if (guide.note) {
    const note = document.createElement("div");
    note.className = "muted-box";
    note.textContent = String(guide.note);
    card.appendChild(note);
  }
}

function renderInlineGuide(previewRoot, guide) {
  if (!guide || typeof guide !== "object") {
    return;
  }
  const card = document.createElement("section");
  card.className = "network-export-guide artifact-guide-inline";
  appendGuide(card, guide);
  previewRoot.appendChild(card);
}

function renderNetworkExportGuide(previewRoot, payload, viewer) {
  const card = document.createElement("section");
  card.className = "network-export-guide";

  const title = document.createElement("h4");
  title.textContent = String(payload.title || `${payload.format || "Network"} export`);
  card.appendChild(title);

  const summary = document.createElement("p");
  summary.textContent = String(payload.summary || "");
  card.appendChild(summary);

  const tools = Array.isArray(payload.recommended_tools) ? payload.recommended_tools : [];
  if (tools.length) {
    const toolsBox = document.createElement("div");
    toolsBox.className = "muted-box";
    toolsBox.textContent = `Recommended tools: ${tools.join(", ")}`;
    card.appendChild(toolsBox);
  }

  const tips = Array.isArray(payload.tips) ? payload.tips : [];
  if (tips.length) {
    const list = document.createElement("ul");
    list.className = "network-export-tips";
    for (const tip of tips) {
      const li = document.createElement("li");
      li.textContent = String(tip);
      list.appendChild(li);
    }
    card.appendChild(list);
  }

  if (payload.download_hint) {
    const hint = document.createElement("div");
    hint.className = "muted-box";
    hint.textContent = String(payload.download_hint);
    card.appendChild(hint);
  }

  if (viewer === "network_cytoscape_script" && payload.text) {
    const codeWrap = document.createElement("div");
    codeWrap.className = "network-export-code";

    const codeHead = document.createElement("div");
    codeHead.className = "network-export-code-head";
    codeHead.textContent = "PYTHON";
    codeWrap.appendChild(codeHead);

    const pre = document.createElement("pre");
    pre.textContent = String(payload.text);
    codeWrap.appendChild(pre);

    if (payload.truncated) {
      const note = document.createElement("div");
      note.className = "muted-box";
      note.textContent = "Preview truncated. Open the file directly from the run directory if needed.";
      card.appendChild(note);
    }

    card.appendChild(codeWrap);
  }

  previewRoot.appendChild(card);
}

function renderTablePreview(previewRoot, payload) {
  const table = document.createElement("table");
  table.className = "preview-table";

  const headers = Array.isArray(payload.headers) ? payload.headers : [];
  const thead = document.createElement("thead");
  const trHead = document.createElement("tr");
  for (const header of headers) {
    const th = document.createElement("th");
    th.textContent = String(header);
    trHead.appendChild(th);
  }
  thead.appendChild(trHead);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const rows = Array.isArray(payload.rows) ? payload.rows : [];
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const cell of row) {
      const td = document.createElement("td");
      td.textContent = String(cell);
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  previewRoot.appendChild(table);

  if (payload.truncated) {
    const note = document.createElement("div");
    note.className = "muted-box";
    note.textContent = `Preview truncated. Showing ${rows.length} of ${payload.total_rows} row(s).`;
    previewRoot.appendChild(note);
  }
}

export function renderFilePreview(payload, ids = {}) {
  const previewRoot = target(ids, "preview");
  const header = target(ids, "header");
  previewRoot.innerHTML = "";

  if (!payload || typeof payload !== "object") {
    header.textContent = "No preview available.";
    return;
  }

  const viewer = payload.viewer || "none";
  header.textContent = `${payload.path || "-"} · ${viewerLabel(viewer)}`;

  if (viewer === "artifact_guide") {
    const card = document.createElement("section");
    card.className = "network-export-guide";
    appendGuide(card, payload);
    previewRoot.appendChild(card);
    return;
  }

  renderInlineGuide(previewRoot, payload.guide);

  if (viewer === "network_gexf" || viewer === "network_graphml" || viewer === "network_cytoscape_script") {
    renderNetworkExportGuide(previewRoot, payload, viewer);
    return;
  }

  if (viewer === "json" || viewer === "text" || viewer === "plan") {
    const pre = document.createElement("pre");
    pre.textContent = payload.text || payload.note || "No text preview.";
    previewRoot.appendChild(pre);
    return;
  }

  if (viewer === "table_csv" || viewer === "table_tsv") {
    renderTablePreview(previewRoot, payload);
    return;
  }

  const pre = document.createElement("pre");
  pre.textContent = "Preview is not available for this file type.";
  previewRoot.appendChild(pre);
}

function entryName(path) {
  const normalized = String(path || "").replace(/^\/+/, "");
  const idx = normalized.lastIndexOf("/");
  return idx >= 0 ? normalized.slice(idx + 1) : normalized;
}

function entryParent(path) {
  const normalized = String(path || "").replace(/^\/+/, "");
  const idx = normalized.lastIndexOf("/");
  return idx >= 0 ? normalized.slice(0, idx) : "";
}

function buildEntriesTree(entries) {
  const root = {
    path: "",
    kind: "dir",
    name: "",
    children: [],
  };
  const nodes = new Map([["", root]]);

  const ensureDir = (dirPath) => {
    const normalized = String(dirPath || "").replace(/^\/+/, "");
    if (nodes.has(normalized)) {
      return nodes.get(normalized);
    }

    const parent = ensureDir(entryParent(normalized));
    const node = {
      path: normalized,
      kind: "dir",
      name: entryName(normalized),
      size_bytes: null,
      viewer: "none",
      visualizable: false,
      children: [],
    };
    nodes.set(normalized, node);
    parent.children.push(node);
    return node;
  };

  const sorted = [...entries].sort((a, b) => String(a.path).localeCompare(String(b.path)));
  for (const entry of sorted) {
    const path = String(entry.path || "").replace(/^\/+/, "");
    if (!path) {
      continue;
    }

    const parent = ensureDir(entryParent(path));
    const existing = nodes.get(path);
    if (entry.kind === "dir") {
      const dirNode = existing || ensureDir(path);
      dirNode.kind = "dir";
      dirNode.name = entryName(path);
      dirNode.size_bytes = entry.size_bytes ?? null;
      dirNode.viewer = entry.viewer || "none";
      dirNode.visualizable = Boolean(entry.visualizable);
      continue;
    }

    const node = {
      path,
      kind: "file",
      name: entryName(path),
      size_bytes: entry.size_bytes ?? null,
      viewer: entry.viewer || "none",
      visualizable: Boolean(entry.visualizable),
      children: [],
    };
    if (existing) {
      Object.assign(existing, node, { children: existing.children || [] });
    } else {
      nodes.set(path, node);
      parent.children.push(node);
    }
  }

  const sortChildren = (node) => {
    node.children.sort((a, b) => {
      const dirWeight = (a.kind === "dir" ? 0 : 1) - (b.kind === "dir" ? 0 : 1);
      if (dirWeight !== 0) {
        return dirWeight;
      }
      return String(a.name).localeCompare(String(b.name));
    });
    for (const child of node.children) {
      if (child.kind === "dir") {
        sortChildren(child);
      }
    }
  };
  sortChildren(root);
  return root;
}

function activeMode(ids) {
  return currentBundleMode(targetId(ids, "bundleMode"));
}

function previewErrorToast(error) {
  pushToast({
    title: "File preview error",
    message: error.message,
    kind: "warning",
    ttlMs: 7000,
  });
}

async function openFileEntry(entry, state, api, mode, ids = {}, options = {}) {
  if (!entry || entry.kind !== "file") {
    return;
  }

  if (entry.viewer === "plan" && typeof options.renderPlanPreview === "function") {
    options.renderPlanPreview(entry.path);
    return;
  }

  const payload = await api.fetchFileContent(entry.path, mode);
  renderFilePreview(payload, ids);
}

function renderTreeNode({ node, depth, state, api, mode, ids, options }) {
  const tree = target(ids, "tree");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "file-node";
  if (node.kind === "dir") {
    button.classList.add("dir");
  }
  if (node.visualizable) {
    button.classList.add("visualizable");
  }
  if (node.path === state.selectedFilePath) {
    button.classList.add("selected");
  }

  button.style.paddingLeft = `${0.65 + depth * 1.05}rem`;
  button.title = node.path;

  const labelSpan = document.createElement("span");
  labelSpan.className = "node-label";

  const toggleSpan = document.createElement("span");
  toggleSpan.className = "toggle-glyph";
  const kindSpan = document.createElement("span");
  kindSpan.className = "kind-glyph";
  const nameSpan = document.createElement("span");
  nameSpan.className = "node-name";
  nameSpan.textContent = node.name;

  if (node.kind === "dir") {
    const collapsed = state.collapsedDirs.has(node.path);
    toggleSpan.textContent = collapsed ? "▸" : "▾";
    kindSpan.textContent = "📁";
  } else {
    toggleSpan.textContent = " ";
    kindSpan.textContent = "📄";
  }
  labelSpan.appendChild(toggleSpan);
  labelSpan.appendChild(kindSpan);
  labelSpan.appendChild(nameSpan);
  button.appendChild(labelSpan);

  const metaBits = [];
  if (node.kind === "file") {
    metaBits.push(formatBytes(node.size_bytes));
    if (node.viewer && node.viewer !== "none") {
      metaBits.push(viewerLabel(node.viewer));
    }
  } else {
    metaBits.push(`${node.children.length} item(s)`);
  }
  if (metaBits.length) {
    const metaSpan = document.createElement("span");
    metaSpan.className = "meta";
    metaSpan.textContent = metaBits.filter(Boolean).join(" · ");
    button.appendChild(metaSpan);
  }

  button.addEventListener("click", async () => {
    if (node.kind === "dir") {
      if (state.collapsedDirs.has(node.path)) {
        state.collapsedDirs.delete(node.path);
      } else {
        state.collapsedDirs.add(node.path);
      }
      renderFilesTree(state, api, ids, options);
      return;
    }

    state.selectedFilePath = node.path;
    renderFilesTree(state, api, ids, options);
    try {
      await openFileEntry(node, state, api, mode || activeMode(ids), ids, options);
    } catch (err) {
      previewErrorToast(err);
    }
  });
  tree.appendChild(button);

  if (node.kind === "dir" && !state.collapsedDirs.has(node.path)) {
    for (const child of node.children) {
      renderTreeNode({
        node: child,
        depth: depth + 1,
        state,
        api,
        mode,
        ids,
        options,
      });
    }
  }
}

export function renderFilesTree(state, api, ids = {}, options = {}) {
  ensureFileState(state);
  const tree = target(ids, "tree");
  tree.innerHTML = "";
  const root = buildEntriesTree(state.filesEntries || []);
  for (const child of root.children) {
    renderTreeNode({
      node: child,
      depth: 0,
      state,
      api,
      mode: state.filesMode || activeMode(ids),
      ids,
      options,
    });
  }
}

export function renderFiles(state, api, entries, mode, ids = {}, options = {}) {
  ensureFileState(state);
  state.filesEntries = Array.isArray(entries) ? [...entries] : [];
  state.filesMode = mode;

  const tree = target(ids, "tree");
  tree.innerHTML = "";
  const list = state.filesEntries;
  const filesCount = list.filter((item) => item.kind === "file").length;
  const dirsCount = list.filter((item) => item.kind === "dir").length;
  target(ids, "summary").textContent = `bundle=${mode} | files=${filesCount} | dirs=${dirsCount}`;

  if (!list.length) {
    const empty = document.createElement("div");
    empty.className = "muted-box";
    empty.textContent = "No files available for this job yet.";
    tree.appendChild(empty);
    return;
  }

  renderFilesTree(state, api, ids, options);
}

function selectPreferredEntry(entries, preferredPathSuffixes = []) {
  const lowerSuffixes = preferredPathSuffixes.map((suffix) => String(suffix).toLowerCase());
  for (const suffix of lowerSuffixes) {
    const match = entries.find(
      (item) => item.kind === "file" && String(item.path || "").toLowerCase().endsWith(suffix)
    );
    if (match) {
      return match;
    }
  }
  return entries.find((item) => item.kind === "file" && item.visualizable) || null;
}

export async function fetchFiles(state, api, ids = {}, options = {}) {
  ensureFileState(state);
  const mode = activeMode(ids);
  const payload = await api.fetchFiles(mode);
  const entries = Array.isArray(payload.entries) ? payload.entries : [];

  if (state.loadedFilesKey === null) {
    state.collapsedDirs = new Set(
      entries
        .filter((item) => item.kind === "dir" && item.path)
        .map((item) => String(item.path))
    );
  }

  renderFiles(state, api, entries, mode, ids, options);
  if ("loadedFilesKey" in state && state.loadedFilesKey === null) {
    state.loadedFilesKey = `${mode}:${entries.length}`;
  }

  const currentExists = entries.some(
    (item) => item.kind === "file" && String(item.path) === String(state.selectedFilePath || "")
  );
  if (currentExists && state.selectedFilePath) {
    const selected = entries.find(
      (item) => item.kind === "file" && String(item.path) === String(state.selectedFilePath)
    );
    if (selected) {
      try {
        await openFileEntry(selected, state, api, mode, ids, options);
      } catch (err) {
        previewErrorToast(err);
      }
    }
    return payload;
  }

  const targetEntry = selectPreferredEntry(entries, options.preferredPathSuffixes || []);
  if (targetEntry) {
    state.selectedFilePath = targetEntry.path;
    renderFiles(state, api, entries, mode, ids, options);
    try {
      await openFileEntry(targetEntry, state, api, mode, ids, options);
    } catch (err) {
      previewErrorToast(err);
    }
  }

  return payload;
}
