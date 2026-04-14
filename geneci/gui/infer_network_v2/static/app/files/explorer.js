import { $, currentBundleMode, formatBytes } from "../core/dom.js";
import { fetchFileContentData, fetchFilesData } from "../core/api.js";
import { state } from "../core/state.js";
import { renderPlanInlinePreview } from "../plan/view.js";
import { pushToast } from "../ui/toasts.js";

export function resetFilesView(message) {
  state.selectedFilePath = null;
  $("files-summary").textContent = message || "No files loaded yet.";
  $("files-tree").innerHTML = "";
  $("file-preview-header").textContent = "Select a file to preview.";
  $("file-preview").innerHTML = "";
}

export function renderFilePreview(payload) {
  const previewRoot = $("file-preview");
  previewRoot.innerHTML = "";
  if (!payload || typeof payload !== "object") {
    $("file-preview-header").textContent = "No preview available.";
    return;
  }

  const viewer = payload.viewer || "none";
  $("file-preview-header").textContent = `${payload.path || "-"} · ${viewer}`;

  if (viewer === "json" || viewer === "text" || viewer === "plan") {
    const pre = document.createElement("pre");
    pre.textContent = payload.text || payload.note || "No text preview.";
    previewRoot.appendChild(pre);
    return;
  }

  const renderTable = () => {
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
  };

  if (viewer === "table_csv" || viewer === "table_tsv") {
    renderTable();
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

    const parentPath = entryParent(normalized);
    const parent = ensureDir(parentPath);
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
    const nextNode = {
      path,
      kind: entry.kind === "dir" ? "dir" : "file",
      name: entryName(path),
      size_bytes: entry.size_bytes ?? null,
      viewer: entry.viewer || "none",
      visualizable: Boolean(entry.visualizable),
      children: existing?.children || [],
    };

    if (!existing) {
      parent.children.push(nextNode);
    }
    nodes.set(path, nextNode);
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

function renderTreeNode({ node, depth, mode }) {
  const tree = $("files-tree");
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
    labelSpan.appendChild(toggleSpan);
    labelSpan.appendChild(kindSpan);
    labelSpan.appendChild(nameSpan);
  } else {
    toggleSpan.textContent = " ";
    kindSpan.textContent = "📄";
    labelSpan.appendChild(toggleSpan);
    labelSpan.appendChild(kindSpan);
    labelSpan.appendChild(nameSpan);
  }
  button.appendChild(labelSpan);

  const metaBits = [];
  if (node.kind === "file") {
    metaBits.push(formatBytes(node.size_bytes));
    if (node.viewer && node.viewer !== "none") {
      metaBits.push(node.viewer);
    }
  } else {
    metaBits.push(`${node.children.length} item(s)`);
  }
  if (metaBits.length) {
    const metaSpan = document.createElement("span");
    metaSpan.className = "meta";
    metaSpan.textContent = metaBits.join(" · ");
    button.appendChild(metaSpan);
  }

  if (node.kind === "dir") {
    button.addEventListener("click", () => {
      if (state.collapsedDirs.has(node.path)) {
        state.collapsedDirs.delete(node.path);
      } else {
        state.collapsedDirs.add(node.path);
      }
      renderFiles(state.filesEntries, mode);
    });
  } else {
    button.addEventListener("click", async () => {
      state.selectedFilePath = node.path;
      renderFiles(state.filesEntries, mode);
      try {
        await openFileEntry(node, mode);
      } catch (err) {
        pushToast({ title: "File preview error", message: err.message, kind: "warning", ttlMs: 7000 });
      }
    });
  }
  tree.appendChild(button);

  if (node.kind === "dir" && !state.collapsedDirs.has(node.path)) {
    for (const child of node.children) {
      renderTreeNode({
        node: child,
        depth: depth + 1,
        mode,
      });
    }
  }
}

export function renderFiles(entries, mode) {
  state.filesEntries = Array.isArray(entries) ? [...entries] : [];
  state.filesMode = mode;

  const tree = $("files-tree");
  tree.innerHTML = "";
  const list = state.filesEntries;
  const filesCount = list.filter((item) => item.kind === "file").length;
  const dirsCount = list.filter((item) => item.kind === "dir").length;
  $("files-summary").textContent = `bundle=${mode} | files=${filesCount} | dirs=${dirsCount}`;

  if (!list.length) {
    const empty = document.createElement("div");
    empty.className = "muted-box";
    empty.textContent = "No files available for this job yet.";
    tree.appendChild(empty);
    return;
  }

  const root = buildEntriesTree(list);
  for (const child of root.children) {
    renderTreeNode({
      node: child,
      depth: 0,
      mode,
    });
  }
}

async function openFileEntry(entry, mode) {
  if (!state.jobId || !entry || entry.kind !== "file") {
    return;
  }

  if (entry.viewer === "plan") {
    renderPlanInlinePreview(state.lastPlan, entry.path);
    return;
  }

  const preview = await fetchFileContentData(state.jobId, entry.path, mode);
  renderFilePreview(preview);
}

export async function fetchFiles(jobId) {
  const mode = currentBundleMode();
  const payload = await fetchFilesData(jobId, mode);
  const entries = Array.isArray(payload.entries) ? payload.entries : [];
  if (state.loadedFilesKey === null) {
    state.collapsedDirs = new Set(
      entries
        .filter((item) => item.kind === "dir" && item.path)
        .map((item) => String(item.path))
    );
  }
  renderFiles(entries, mode);
  state.loadedFilesKey = `${jobId}:${mode}:${entries.length}`;

  const currentExists = entries.some(
    (item) => item.kind === "file" && String(item.path) === String(state.selectedFilePath || "")
  );
  if (currentExists && state.selectedFilePath) {
    const selected = entries.find(
      (item) => item.kind === "file" && String(item.path) === String(state.selectedFilePath)
    );
    if (selected) {
      try {
        await openFileEntry(selected, mode);
      } catch (err) {
        pushToast({ title: "File preview error", message: err.message, kind: "warning", ttlMs: 7000 });
      }
    }
    return;
  }

  const preferred = entries.find(
    (item) => item.kind === "file" && String(item.path).toLowerCase().endsWith("run/merged_network_normalized.csv")
  );
  const fallback = entries.find((item) => item.kind === "file" && item.visualizable);
  const target = preferred || fallback || null;
  if (target) {
    state.selectedFilePath = target.path;
    renderFiles(entries, mode);
    try {
      await openFileEntry(target, mode);
    } catch (err) {
      pushToast({ title: "File preview error", message: err.message, kind: "warning", ttlMs: 7000 });
    }
  }
}
