import { $ } from "../core/dom.js";

export function updatePreflightSummary(preflightReport = null) {
  const viewEl = $("preflight-report-view");
  if (!viewEl) {
    return;
  }
  if (!preflightReport || !preflightReport.catalog) {
    viewEl.textContent = "No preflight report yet.";
    return;
  }
  viewEl.innerHTML = "";

  const kpiGrid = document.createElement("div");
  kpiGrid.className = "preflight-grid";
  const kpis = [
    { label: "Dataset", value: String(preflightReport?.dataset?.dataset_id || "-") },
    { label: "Expression", value: `${preflightReport?.dataset?.genes ?? "-"} × ${preflightReport?.dataset?.columns ?? "-"}` },
  ];
  for (const item of kpis) {
    const card = document.createElement("article");
    card.className = "preflight-kpi";
    const strong = document.createElement("strong");
    strong.textContent = item.label;
    const span = document.createElement("span");
    span.textContent = item.value;
    card.appendChild(strong);
    card.appendChild(span);
    kpiGrid.appendChild(card);
  }
  viewEl.appendChild(kpiGrid);

  const validation = preflightReport.input_validation || {};
  const exprValidation = validation.expression_matrix || {};
  const extrasValidation = validation.extras || {};
  const validationList = document.createElement("section");
  validationList.className = "preflight-list";
  validationList.innerHTML = "<h4>Input Validation</h4>";
  const exprErrors = Array.isArray(exprValidation.errors) ? exprValidation.errors : [];
  const exprWarnings = Array.isArray(exprValidation.warnings) ? exprValidation.warnings : [];
  const exprDetail = exprErrors[0] || exprWarnings[0] || "";
  const exprLine = document.createElement("div");
  exprLine.className = "preflight-list-line";
  exprLine.textContent = `expression_matrix: ${exprValidation.status || "unknown"}${
    exprDetail ? ` (${exprDetail})` : ""
  }`;
  validationList.appendChild(exprLine);
  const extraKeys = Object.keys(extrasValidation).sort();
  for (const key of extraKeys) {
    const item = extrasValidation[key] || {};
    const status = item.status || "unknown";
    const errors = Array.isArray(item.errors) ? item.errors : [];
    const warns = Array.isArray(item.warnings) ? item.warnings : [];
    const detail = errors[0] || warns[0] || "";
    const line = document.createElement("div");
    line.className = "preflight-list-line";
    line.textContent = `${key}: ${status}${detail ? ` (${detail})` : ""}`;
    validationList.appendChild(line);
  }
  viewEl.appendChild(validationList);

  const warningsList = document.createElement("section");
  warningsList.className = "preflight-list";
  warningsList.innerHTML = "<h4>Warnings</h4>";
  const warnings = Array.isArray(preflightReport.warnings) ? preflightReport.warnings : [];
  if (!warnings.length) {
    const line = document.createElement("div");
    line.className = "preflight-list-line";
    line.textContent = "No warnings.";
    warningsList.appendChild(line);
  } else {
    for (const warningText of warnings.slice(0, 8)) {
      const line = document.createElement("div");
      line.className = "preflight-list-line";
      line.textContent = `• ${String(warningText)}`;
      warningsList.appendChild(line);
    }
    if (warnings.length > 8) {
      const line = document.createElement("div");
      line.className = "preflight-list-line";
      line.textContent = `... ${warnings.length - 8} more`;
      warningsList.appendChild(line);
    }
  }
  viewEl.appendChild(warningsList);

  const rawDetails = document.createElement("details");
  rawDetails.className = "preflight-list";
  const summaryNode = document.createElement("summary");
  summaryNode.textContent = "Raw preflight_report.json";
  rawDetails.appendChild(summaryNode);
  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(preflightReport, null, 2);
  rawDetails.appendChild(pre);
  viewEl.appendChild(rawDetails);
}
