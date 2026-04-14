async function readJson(response, fallbackMessage) {
  let payload = null;
  try {
    payload = await response.json();
  } catch (_err) {
    payload = null;
  }
  if (!response.ok) {
    throw new Error(payload?.detail || fallbackMessage || `Request failed (${response.status})`);
  }
  return payload;
}

export async function fetchBootstrapData() {
  const response = await fetch("/api/infer-network-v2/bootstrap");
  return readJson(response, `Failed to load bootstrap data (${response.status})`);
}

export async function submitPreflightRequest(formData) {
  const response = await fetch("/api/infer-network-v2/preflight", {
    method: "POST",
    body: formData,
  });
  return readJson(response, "Preflight submission failed");
}

export async function submitPlanRequest(body) {
  const response = await fetch("/api/infer-network-v2/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return readJson(response, "Plan submission failed");
}

export async function submitRunRequest(body) {
  const response = await fetch("/api/infer-network-v2/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return readJson(response, "Run submission failed");
}

export async function fetchJobData(jobId) {
  const response = await fetch(`/api/infer-network-v2/jobs/${jobId}`);
  return readJson(response, `Failed to load job status (${response.status})`);
}

export async function fetchPlanData(jobId) {
  const response = await fetch(`/api/infer-network-v2/jobs/${jobId}/plan`);
  return readJson(response, `Failed to load plan (${response.status})`);
}

export async function fetchFilesData(jobId, mode) {
  const response = await fetch(`/api/infer-network-v2/jobs/${jobId}/files?mode=${encodeURIComponent(mode)}`);
  return readJson(response, `Failed to load files (${response.status})`);
}

export async function fetchFileContentData(jobId, virtualPath, mode) {
  const response = await fetch(
    `/api/infer-network-v2/jobs/${jobId}/file-content?mode=${encodeURIComponent(mode)}&path=${encodeURIComponent(
      virtualPath
    )}`
  );
  return readJson(response, `Failed to load file preview (${response.status})`);
}
