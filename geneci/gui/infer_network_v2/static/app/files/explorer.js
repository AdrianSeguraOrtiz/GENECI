import {
  fetchFiles as fetchCommonFiles,
  renderFilePreview,
  renderFiles as renderCommonFiles,
  resetFilesView as resetCommonFilesView,
} from "/static-common/app/files/explorer.js?v=20260423a";
import { fetchFileContentData, fetchFilesData } from "../core/api.js";
import { state } from "../core/state.js";
import { renderPlanInlinePreview } from "../plan/view.js";

function fileApi(jobId) {
  return {
    fetchFiles: (mode) => fetchFilesData(jobId, mode),
    fetchFileContent: (path, mode) => fetchFileContentData(jobId, path, mode),
  };
}

function explorerOptions() {
  return {
    preferredPathSuffixes: ["run/merged_network_normalized.csv"],
    renderPlanPreview: (path) => renderPlanInlinePreview(state.lastPlan, path),
  };
}

export { renderFilePreview };

export function resetFilesView(message) {
  resetCommonFilesView(state, message);
}

export function renderFiles(entries, mode) {
  renderCommonFiles(state, fileApi(state.jobId), entries, mode, {}, explorerOptions());
}

export async function fetchFiles(jobId) {
  state.jobId = jobId || state.jobId;
  return fetchCommonFiles(state, fileApi(state.jobId), {}, explorerOptions());
}
