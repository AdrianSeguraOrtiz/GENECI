import { state } from "../core/state.js";

export function toolById(toolId) {
  const tools = Array.isArray(state.bootstrap?.tools) ? state.bootstrap.tools : [];
  return tools.find((item) => item.tool_id === toolId) || null;
}

export function listAvailableTools() {
  const tools = Array.isArray(state.bootstrap?.tools) ? state.bootstrap.tools : [];
  if (!Array.isArray(state.eligibleToolIds) || !state.eligibleToolIds.length) {
    return [];
  }
  const allowed = new Set(state.eligibleToolIds);
  return tools.filter((tool) => allowed.has(tool.tool_id));
}

export function defaultGroupModeForTool(tool) {
  return String(tool?.execution_scope || "").trim() === "group" ? "per_group" : "global";
}

export function toolMessages(entry) {
  const toolId = String(entry?.tool_id || "").trim();
  const reasons = Array.isArray(entry?.reasons) ? entry.reasons : [];
  const warnings = Array.isArray(entry?.warnings) ? entry.warnings : [];
  const pendingConditions = Array.isArray(entry?.pending_conditions) ? entry.pending_conditions : [];
  const out = [];
  const seen = new Set();
  const prefix = toolId ? `[${toolId}] skipped due to incompatibility:` : "";
  const rawMessages = [...reasons, ...warnings, ...pendingConditions];

  for (const raw of rawMessages) {
    const text = String(raw || "").trim();
    if (!text) {
      continue;
    }
    const expanded = prefix && text.startsWith(prefix)
      ? text
          .slice(prefix.length)
          .split(";")
          .map((item) => item.trim())
          .filter(Boolean)
      : [text];
    for (const message of expanded) {
      if (seen.has(message)) {
        continue;
      }
      seen.add(message);
      out.push(message);
    }
  }
  return out;
}

export function toolSpecInfoPayload(tool) {
  const accepts = Array.isArray(tool?.accepts) ? tool.accepts : [];
  const requiredExtras = Array.isArray(tool?.required_extras) ? tool.required_extras : [];
  const optionalExtras = Array.isArray(tool?.optional_extras) ? tool.optional_extras : [];
  const conditionalExtras = Array.isArray(tool?.conditional_required_extras) ? tool.conditional_required_extras : [];
  const publication = Array.isArray(tool?.publication) ? tool.publication : [];
  const firstAuthor = String(tool?.first_author || "").trim();
  const outputs = tool?.outputs && typeof tool.outputs === "object" ? tool.outputs : {};
  const progress = tool?.progress && typeof tool.progress === "object" ? tool.progress : {};
  const conditionalSummary = conditionalExtras
    .map((item) => String(item?.message || "").trim())
    .filter(Boolean);

  const publicationLinks = publication.map((item) => ({
    label: String(item || "").trim(),
    url: String(item || "").trim(),
  }));
  return {
    title: tool?.name || tool?.tool_id || "Tool Info",
    description: "",
    fields: [
      { label: "Tool ID", value: tool?.tool_id || "-" },
      { label: "Execution Scope", value: tool?.execution_scope || "-" },
      { label: "Assumes", value: tool?.assumes || "-" },
      { label: "Accepts", value: accepts.length ? accepts.join(", ") : "-" },
      { label: "Required extras", value: requiredExtras.length ? requiredExtras.join(", ") : "none" },
      { label: "Optional extras", value: optionalExtras.length ? optionalExtras.join(", ") : "none" },
      { label: "Conditional extras", value: conditionalSummary.length ? conditionalSummary.join(" | ") : "none" },
      {
        label: "Outputs",
        value: `directed=${String(outputs.directed ?? "-")}, sign=${outputs.sign ?? "-"}, evidence=${outputs.evidence ?? "-"}`,
      },
      {
        label: "Progress",
        value: `${progress.kind || "-"}${progress.note ? ` (${String(progress.note)})` : ""}`,
      },
      {
        label: "Implementation",
        link: {
          label: String(tool?.implementation_url || "-"),
          url: String(tool?.implementation_url || ""),
        },
        value: tool?.implementation_url || "-",
      },
      { label: "Docker image", value: tool?.docker_image || "-" },
      { label: "First author", value: firstAuthor || "-" },
      {
        label: "Publication(s)",
        links: publicationLinks.length ? publicationLinks : [{ label: "-", url: "" }],
      },
    ],
    example: "",
  };
}

export function populateToolIssueSelect() {
  const select = document.getElementById("tool-issue-tool-id");
  if (!select) {
    return;
  }
  const tools = Array.isArray(state.bootstrap?.tools) ? [...state.bootstrap.tools] : [];
  tools.sort((a, b) => String(a.name || "").localeCompare(String(b.name || "")));
  select.innerHTML = "";
  for (const tool of tools) {
    const option = document.createElement("option");
    option.value = String(tool.tool_id || "");
    option.textContent = String(tool.name || tool.tool_id || "");
    select.appendChild(option);
  }
}

export function buildToolRequestIssueUrl() {
  const toolName = String(document.getElementById("tool-request-tool-name")?.value || "").trim();
  const doi = String(document.getElementById("tool-request-doi")?.value || "").trim();
  const repoUrl = String(document.getElementById("tool-request-repo")?.value || "").trim();
  const expectedInputs = String(document.getElementById("tool-request-inputs")?.value || "").trim();
  const expectedOutputs = String(document.getElementById("tool-request-outputs")?.value || "").trim();
  const notes = String(document.getElementById("tool-request-notes")?.value || "").trim();

  if (!toolName) {
    throw new Error("Tool Name is required to create the issue.");
  }

  const issueTitle = `[Tool Request] ${toolName}`;
  const bodyLines = [
    "## Tool Request",
    "",
    `- Tool name: ${toolName}`,
    `- DOI / publication: ${doi || "-"}`,
    `- Implementation repository: ${repoUrl || "-"}`,
    `- Expected inputs: ${expectedInputs || "-"}`,
    `- Expected outputs: ${expectedOutputs || "-"}`,
    "",
    "## Notes",
    notes || "-",
    "",
    "## Submitted From",
    "- GENECI GUI infer-network-v2",
  ];

  const params = new URLSearchParams();
  params.set("title", issueTitle);
  params.set("body", bodyLines.join("\n"));
  params.set("labels", "tool-request");

  return `https://github.com/AdrianSeguraOrtiz/GENECI/issues/new?${params.toString()}`;
}

export function buildToolIssueReportUrl() {
  const toolId = String(document.getElementById("tool-issue-tool-id")?.value || "").trim();
  const issueType = String(document.getElementById("tool-issue-type")?.value || "other").trim();
  const observed = String(document.getElementById("tool-issue-observed")?.value || "").trim();
  const expected = String(document.getElementById("tool-issue-expected")?.value || "").trim();
  const context = String(document.getElementById("tool-issue-context")?.value || "").trim();

  if (!toolId) {
    throw new Error("Select a tool to report.");
  }
  if (!observed) {
    throw new Error("Observed Behavior is required.");
  }
  const tool = toolById(toolId);
  const toolName = String(tool?.name || toolId);

  const issueTitle = `[Tool Catalog Issue] ${toolName} (${issueType})`;
  const bodyLines = [
    "## Tool Catalog Issue",
    "",
    `- tool_id: ${toolId}`,
    `- tool_name: ${toolName}`,
    `- issue_type: ${issueType}`,
    "",
    "## Observed",
    observed,
    "",
    "## Expected",
    expected || "-",
    "",
    "## Context",
    context || "-",
    "",
    "## Submitted From",
    "- GENECI GUI infer-network-v2",
  ];

  const params = new URLSearchParams();
  params.set("title", issueTitle);
  params.set("body", bodyLines.join("\n"));
  params.set("labels", "tool-catalog-issue");
  return `https://github.com/AdrianSeguraOrtiz/GENECI/issues/new?${params.toString()}`;
}
