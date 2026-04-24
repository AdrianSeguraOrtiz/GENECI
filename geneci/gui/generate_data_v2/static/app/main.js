import { $ } from "/static-common/app/core/dom.js";
import { fetchFiles, resetFilesView } from "/static-common/app/files/explorer.js?v=20260423a";
import {
  deepEqualJson,
  readParamsFromHost,
  renderParamsHost,
  resolvedDefaultParams,
} from "/static-common/app/params/schema_form.js?v=20260423c";
import {
  initReproducibility,
  renderReproducibility,
  resetReproducibility,
} from "/static-common/app/repro/view.js";
import {
  pushRuntimeFailureToasts,
  renderRuntimeProgress,
} from "/static-common/app/runtime/view.js";
import { buildInfoTooltip, initInfoPopover, showInfoTooltip } from "/static-common/app/ui/popovers.js";
import { setActiveStep, setStepState, initSteps } from "/static-common/app/ui/steps.js";
import { pushToast } from "/static-common/app/ui/toasts.js";

const state = {
  bootstrap: null,
  simulatorsById: new Map(),
  jobId: null,
  currentJob: null,
  preflightReport: null,
  pollTimer: null,
  selectedFilePath: null,
  filesEntries: [],
  filesMode: "full",
  collapsedDirs: new Set(),
  loadedFilesKey: null,
  paramsModalCard: null,
  notifiedFailures: new Set(),
};

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

async function fetchBootstrapData() {
  const response = await fetch("/api/generate-data-v2/bootstrap");
  return readJson(response, "Failed to load bootstrap data");
}

async function submitPreflight(formData) {
  const response = await fetch("/api/generate-data-v2/preflight", { method: "POST", body: formData });
  return readJson(response, "Preflight submission failed");
}

async function submitPlan(body) {
  const response = await fetch("/api/generate-data-v2/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return readJson(response, "Plan submission failed");
}

async function submitRun(body) {
  const response = await fetch("/api/generate-data-v2/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return readJson(response, "Run submission failed");
}

async function fetchJob(jobId) {
  const response = await fetch(`/api/generate-data-v2/jobs/${jobId}`);
  return readJson(response, "Failed to load job status");
}

async function fetchPlan(jobId) {
  const response = await fetch(`/api/generate-data-v2/jobs/${jobId}/plan`);
  return readJson(response, "Failed to load plan");
}

function fileApi() {
  return {
    fetchFiles: async (mode) => {
      const response = await fetch(`/api/generate-data-v2/jobs/${state.jobId}/files?mode=${encodeURIComponent(mode)}`);
      return readJson(response, "Failed to load files");
    },
    fetchFileContent: async (path, mode) => {
      const response = await fetch(
        `/api/generate-data-v2/jobs/${state.jobId}/file-content?mode=${encodeURIComponent(mode)}&path=${encodeURIComponent(path)}`
      );
      return readJson(response, "Failed to load file preview");
    },
  };
}

function fileExplorerOptions() {
  return {
    preferredPathSuffixes: ["benchmark/benchmark-manifest.json"],
  };
}

function simulatorById(id) {
  return state.simulatorsById.get(String(id || ""));
}

function profileSpec(profileId) {
  return (state.bootstrap?.profiles || []).find((item) => item.id === profileId) || null;
}

function extraByKey(key) {
  return (state.bootstrap?.extras || []).find((item) => item.key === key) || null;
}

function selectedProfileId() {
  return state.preflightReport?.scenario?.profile || $("profile").value;
}

function nativeOutputDefsForSimulator(simulator, profileId = selectedProfileId()) {
  const profileCapabilities = simulator?.profile_capabilities && typeof simulator.profile_capabilities === "object"
    ? simulator.profile_capabilities
    : {};
  const capability = profileCapabilities?.[profileId];
  return Array.isArray(capability?.native_outputs)
    ? capability.native_outputs.filter((item) => item && typeof item === "object" && String(item.id || "").trim())
    : [];
}

function nativeOutputLabel(definitionOrId) {
  if (!definitionOrId) {
    return "-";
  }
  if (typeof definitionOrId === "string") {
    return definitionOrId;
  }
  return String(definitionOrId.id || "-");
}

function readNativeOutputsFromHost(host) {
  if (!host) {
    return [];
  }
  return Array.from(host.querySelectorAll(".native-output-checkbox:checked"))
    .map((node) => String(node.value || "").trim())
    .filter(Boolean);
}

function renderNativeOutputsHost(host, simulator, selected = []) {
  host.innerHTML = "";
  const defs = nativeOutputDefsForSimulator(simulator);
  if (!defs.length) {
    const empty = document.createElement("div");
    empty.className = "muted-box";
    empty.textContent = "No simulator-specific native outputs are available for this profile.";
    host.appendChild(empty);
    return;
  }
  const selectedSet = new Set((selected || []).map((item) => String(item || "").trim()).filter(Boolean));
  const grid = document.createElement("div");
  grid.className = "native-output-grid";
  for (const def of defs) {
    const row = document.createElement("label");
    row.className = "native-output-row";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.className = "native-output-checkbox";
    input.value = String(def.id);
    input.checked = selectedSet.has(String(def.id));

    const meta = document.createElement("div");
    meta.className = "native-output-meta";

    const title = document.createElement("div");
    title.className = "native-output-title";
    const name = document.createElement("strong");
    name.textContent = nativeOutputLabel(def);
    title.appendChild(name);

    const desc = document.createElement("div");
    desc.className = "native-output-desc";
    const formats = Array.isArray(def.formats) && def.formats.length ? ` Formats: ${def.formats.join(", ")}.` : "";
    desc.textContent = `${String(def.description || "").trim()}${formats}`.trim();

    meta.appendChild(title);
    meta.appendChild(desc);

    if (def.notes) {
      const notes = document.createElement("div");
      notes.className = "native-output-notes";
      notes.textContent = String(def.notes);
      meta.appendChild(notes);
    }

    row.appendChild(input);
    row.appendChild(meta);
    grid.appendChild(row);
  }
  host.appendChild(grid);
}

function updateRunNativeOutputsSummary(card, simulator, selected = null) {
  const summary = card.querySelector(".run-native-outputs-summary");
  if (!summary) {
    return;
  }
  const defs = nativeOutputDefsForSimulator(simulator);
  if (!defs.length) {
    summary.textContent = "No simulator-specific native outputs available for this profile.";
    return;
  }
  const selectedIds = selected || readNativeOutputsFromHost(card.querySelector(".run-native-outputs-form"));
  if (!selectedIds.length) {
    summary.textContent = "No native outputs selected.";
    return;
  }
  const defsById = new Map(defs.map((item) => [String(item.id), item]));
  summary.textContent = selectedIds
    .map((outputId) => nativeOutputLabel(defsById.get(String(outputId)) || String(outputId)))
    .join(", ");
}

function renderCardNativeOutputs(card, simulator, selected = null) {
  const host = card.querySelector(".run-native-outputs-form");
  renderNativeOutputsHost(host, simulator, selected || []);
  updateRunNativeOutputsSummary(card, simulator, readNativeOutputsFromHost(host));
}

function simulatorInputById(inputId) {
  return (state.bootstrap?.simulator_inputs || []).find((item) => item.id === inputId) || null;
}

function checkedExtras() {
  return Array.from(document.querySelectorAll(".extra-checkbox:checked")).map((node) => node.value);
}

function resetScenarioDerivedState() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
  state.jobId = null;
  state.currentJob = null;
  state.preflightReport = null;
  state.notifiedFailures = new Set();
  state.loadedFilesKey = null;
  $("runs-container").innerHTML = "";
  updateRunsEmptyState();
  renderSimulatorEligibility(null);
  renderPlan(null);
  renderRuntimeProgress(null);
  renderExecutionAlerts(null);
  updateExplorerVisibility(null);
  syncButtons();
}

function renderExtras() {
  const host = $("extras-grid");
  host.innerHTML = "";
  const selectedProfile = $("profile").value;
  const profile = profileSpec(selectedProfile);
  const required = new Set(profile?.required_extras || []);
  const available = (profile?.available_extras || [])
    .map((key) => extraByKey(key))
    .filter(Boolean);
  $("extras-empty").hidden = available.length > 0;
  for (const extra of available) {
    const row = document.createElement("label");
    row.className = "checkbox-row";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.className = "extra-checkbox";
    input.value = extra.key;
    input.checked = required.has(extra.key);
    input.disabled = required.has(extra.key);
    input.addEventListener("change", resetScenarioDerivedState);
    const text = document.createElement("span");
    const title = document.createElement("div");
    title.className = "checkbox-title";
    title.textContent = extra.label;
    const desc = document.createElement("div");
    desc.className = "checkbox-desc";
    desc.textContent = required.has(extra.key)
      ? `${extra.description} Required by ${selectedProfile}.`
      : extra.description;
    text.appendChild(title);
    text.appendChild(desc);
    row.appendChild(input);
    row.appendChild(text);
    host.appendChild(row);
  }
}

function initBootstrapView() {
  const profileSelect = $("profile");
  profileSelect.innerHTML = "";
  for (const profile of state.bootstrap.profiles || []) {
    const option = document.createElement("option");
    option.value = profile.id;
    option.textContent = profile.id;
    profileSelect.appendChild(option);
  }
  if ((state.bootstrap.profiles || []).some((item) => item.id === "scrna_grouped")) {
    profileSelect.value = "scrna_grouped";
  }
  profileSelect.addEventListener("change", renderExtras);
  profileSelect.addEventListener("change", resetScenarioDerivedState);
  const defaultMaxParallel = Number.parseInt(
    String(state.bootstrap?.planning_defaults?.max_parallel_tasks || ""),
    10
  );
  if (Number.isInteger(defaultMaxParallel) && defaultMaxParallel >= 1) {
    $("max-parallel-tasks").value = String(defaultMaxParallel);
  }
  renderExtras();
  populateSimulatorIssueSelect();
}

function addInputRow() {
  const template = $("input-template");
  const node = template.content.firstElementChild.cloneNode(true);
  const select = node.querySelector(".input-kind");
  select.innerHTML = "";
  for (const item of state.bootstrap.simulator_inputs || []) {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.label || item.id;
    select.appendChild(option);
  }
  const updateDescription = () => {
    const meta = simulatorInputById(select.value);
    const description = node.querySelector(".input-kind-description");
    const formats = Array.isArray(meta?.formats) && meta.formats.length ? ` Formats: ${meta.formats.join(", ")}.` : "";
    const columns = Array.isArray(meta?.required_columns) && meta.required_columns.length
      ? ` Required columns: ${meta.required_columns.join(", ")}.`
      : "";
    description.textContent = `${meta?.description || ""}${formats}${columns}`.trim() || "Input file.";
    node.querySelector(".input-file").accept = String(meta?.accept || "");
    updateOrganismRequirement(node);
    resetScenarioDerivedState();
  };
  select.addEventListener("change", updateDescription);
  node.querySelector(".input-file").addEventListener("change", resetScenarioDerivedState);
  node.querySelector(".organism-kind")?.addEventListener("change", resetScenarioDerivedState);
  node.querySelector(".organism-tax-id")?.addEventListener("input", resetScenarioDerivedState);
  node.querySelector(".organism-name")?.addEventListener("input", resetScenarioDerivedState);
  node.querySelector(".remove-input").addEventListener("click", () => {
    node.remove();
    updateInputsEmptyState();
    updateOrganismRequirement();
    resetScenarioDerivedState();
  });
  $("inputs-list").appendChild(node);
  updateDescription();
  updateInputsEmptyState();
}

function updateInputsEmptyState() {
  $("inputs-empty").style.display = selectedInputRows().length ? "none" : "block";
}

function selectedInputRows() {
  return Array.from(document.querySelectorAll("#inputs-list .extra-row"));
}

function rowRequiresOrganism(row) {
  const meta = simulatorInputById(row.querySelector(".input-kind")?.value);
  return Boolean(meta?.requires_organism);
}

function updateOrganismRequirement(row = null) {
  const rows = row ? [row] : selectedInputRows();
  for (const currentRow of rows) {
    const box = currentRow.querySelector(".input-organism-box");
    const required = rowRequiresOrganism(currentRow);
    if (!box) {
      continue;
    }
    box.hidden = !required;
    currentRow.classList.toggle("requires-organism", required);
    if (required) {
      box.open = true;
    }
  }
}

function rowOrganismPayload(row) {
  const kind = row.querySelector(".organism-kind")?.value || "synthetic";
  const taxIdRaw = row.querySelector(".organism-tax-id")?.value.trim() || "";
  const name = row.querySelector(".organism-name")?.value.trim() || "";
  const organism = {
    kind,
    tax_id: taxIdRaw ? Number.parseInt(taxIdRaw, 10) : null,
  };
  if (name) {
    organism.name = name;
  }
  return organism;
}

function validateScenarioForm() {
  const benchmarkId = $("benchmark-id").value.trim();
  if (!benchmarkId) {
    throw new Error("Benchmark ID is required.");
  }
  const seenInputs = new Set();
  for (const row of selectedInputRows()) {
    const inputId = row.querySelector(".input-kind").value;
    const label = simulatorInputById(inputId)?.label || inputId;
    if (seenInputs.has(inputId)) {
      throw new Error(`Duplicate input file type: ${label}`);
    }
    seenInputs.add(inputId);
    if (!row.querySelector(".input-file").files?.[0]) {
      throw new Error(`Input file is required for ${label}.`);
    }
    if (rowRequiresOrganism(row)) {
      const organism = rowOrganismPayload(row);
      if (!organism.name && !organism.tax_id) {
        throw new Error(`Organism name or tax_id is required for ${label}.`);
      }
      if (organism.kind === "biological" && !organism.tax_id) {
        throw new Error(`Tax ID is required when organism kind is biological for ${label}.`);
      }
    }
  }
}

function collectScenarioConfig() {
  const organismRow = selectedInputRows().find((row) => rowRequiresOrganism(row)) || null;
  const organism = organismRow
    ? rowOrganismPayload(organismRow)
    : { kind: "synthetic", tax_id: null };
  const scenario = {
    id: $("benchmark-id").value.trim(),
    profile: $("profile").value,
    requested_extras: checkedExtras(),
    organism,
  };
  const baseSeed = $("base-seed").value.trim();
  if (baseSeed) {
    scenario.base_seed = Number.parseInt(baseSeed, 10);
  }
  const inputs = {};
  selectedInputRows().forEach((row) => {
    const inputId = row.querySelector(".input-kind").value.trim();
    if (!inputId) {
      return;
    }
    const meta = simulatorInputById(inputId) || {};
    inputs[inputId] = {
      path: `uploaded:${inputId}`,
      format: Array.isArray(meta.formats) && meta.formats.length ? meta.formats[0] : undefined,
      description: meta.description || undefined,
    };
    if (rowRequiresOrganism(row)) {
      inputs[inputId].organism = rowOrganismPayload(row);
    }
    const description = row.querySelector(".input-description").value.trim();
    if (description) {
      inputs[inputId].description = description;
    }
  });
  if (Object.keys(inputs).length) {
    scenario.inputs = inputs;
  }
  return {
    scenario,
    options: {
      output_dir: $("output-dir").value.trim() || "./benchmarks_v2",
    },
  };
}

function buildPreflightFormData() {
  validateScenarioForm();
  const formData = new FormData();
  formData.append("config", JSON.stringify(collectScenarioConfig()));
  selectedInputRows().forEach((row) => {
    const inputId = row.querySelector(".input-kind").value.trim();
    const file = row.querySelector(".input-file").files?.[0];
    if (inputId && file) {
      formData.append(`input__${inputId}`, file);
    }
  });
  return formData;
}

function simulatorInfoPayload(simulator) {
  const profileCapabilities = simulator.profile_capabilities && typeof simulator.profile_capabilities === "object"
    ? simulator.profile_capabilities
    : {};
  const publications = Array.isArray(simulator.publication) ? simulator.publication : [];
  const rawInputs = simulator.simulator_inputs && typeof simulator.simulator_inputs === "object"
    ? simulator.simulator_inputs
    : {};
  const inputIds = [
    ...(Array.isArray(rawInputs.required) ? rawInputs.required : []),
    ...(Array.isArray(rawInputs.optional) ? rawInputs.optional : []),
    ...(Array.isArray(rawInputs.conditional_required) ? rawInputs.conditional_required : []),
  ]
    .map((item) => String(item?.id || item?.input || "").trim())
    .filter(Boolean);
  return buildInfoTooltip({
    title: simulator.name,
    description: simulator.simulation_summary || "",
    fields: [
      { label: "Simulator ID", value: simulator.simulator_id || "-" },
      {
        label: "Supported profiles",
        value: Object.keys(profileCapabilities).length ? Object.keys(profileCapabilities).join(", ") : "-",
      },
      { label: "Simulator inputs", value: inputIds.length ? [...new Set(inputIds)].join(", ") : "none" },
      { label: "Keywords", value: (simulator.simulation_keywords || []).join(", ") || "-" },
      {
        label: "Implementation",
        link: {
          label: String(simulator.implementation_url || "-"),
          url: String(simulator.implementation_url || ""),
        },
        value: simulator.implementation_url || "-",
      },
      { label: "Docker image", value: simulator.docker_image || "-" },
      { label: "First author", value: simulator.first_author || "-" },
      {
        label: "Publication(s)",
        links: publications.length
          ? publications.map((item) => ({ label: String(item || "").trim(), url: String(item || "").trim() }))
          : [{ label: "-", url: "" }],
      },
    ],
    example: "",
  });
}

function profileDerivations(capability) {
  const items = Array.isArray(capability?.derivations) ? capability.derivations : [];
  const derivations = new Map();
  for (const item of items) {
    const artifact = String(item?.artifact || "").trim();
    if (artifact && !derivations.has(artifact)) {
      derivations.set(artifact, item);
    }
  }
  return derivations;
}

function artifactDisplayLabel(artifact) {
  const extra = extraByKey(artifact);
  if (extra?.label) {
    return extra.label;
  }
  const truthLabels = {
    global_network: "global_network.csv",
    legacy_binary_matrix: "legacy_binary_matrix",
    group_networks: "group_networks/*.csv",
  };
  return truthLabels[artifact] || artifact;
}

function appendArtifactChipRow(host, items, { derivations, simulator, profileId }) {
  if (!items.length) {
    const empty = document.createElement("span");
    empty.className = "artifact-empty";
    empty.textContent = "none";
    host.appendChild(empty);
    return;
  }
  for (const item of items) {
    const artifact = String(item.artifact || "").trim();
    if (!artifact) {
      continue;
    }
    const chip = document.createElement("span");
    chip.className = `artifact-chip mode-${item.mode || "none"}`;
    const text = document.createElement("span");
    text.textContent = String(item.label || artifactDisplayLabel(artifact));
    chip.appendChild(text);
    const derivation = derivations.get(artifact);
    if (item.mode === "derivable" && derivation) {
      const infoBtn = document.createElement("button");
      infoBtn.type = "button";
      infoBtn.className = "artifact-chip-info";
      infoBtn.textContent = "i";
      infoBtn.title = `How ${artifact} is derived`;
      infoBtn.addEventListener("click", (event) => {
        event.stopPropagation();
        const detailBox = host.closest(".simulator-capability-card")?.querySelector(".simulator-derivation-detail");
        if (!detailBox) {
          return;
        }
        const currentArtifact = detailBox.dataset.artifact || "";
        if (!detailBox.hidden && currentArtifact === artifact) {
          detailBox.hidden = true;
          detailBox.innerHTML = "";
          detailBox.dataset.artifact = "";
          return;
        }
        detailBox.hidden = false;
        detailBox.dataset.artifact = artifact;
        detailBox.innerHTML = "";

        const title = document.createElement("div");
        title.className = "simulator-derivation-head";
        const titleText = document.createElement("strong");
        titleText.textContent = `${artifactDisplayLabel(artifact)} derivation`;
        const closeBtn = document.createElement("button");
        closeBtn.type = "button";
        closeBtn.className = "simulator-derivation-close";
        closeBtn.textContent = "x";
        closeBtn.addEventListener("click", () => {
          detailBox.hidden = true;
          detailBox.innerHTML = "";
          detailBox.dataset.artifact = "";
        });
        title.appendChild(titleText);
        title.appendChild(closeBtn);
        detailBox.appendChild(title);

        const method = document.createElement("p");
        method.className = "simulator-derivation-method";
        method.textContent = String(derivation.method || "").trim();
        detailBox.appendChild(method);

        const sections = [
          ["Source artifacts", Array.isArray(derivation.source_artifacts) ? derivation.source_artifacts : []],
          ["Assumptions", Array.isArray(derivation.assumptions) ? derivation.assumptions : []],
          ["Limitations", Array.isArray(derivation.limitations) ? derivation.limitations : []],
        ];
        for (const [label, values] of sections) {
          const block = document.createElement("div");
          block.className = "simulator-derivation-block";
          const blockTitle = document.createElement("strong");
          blockTitle.textContent = label;
          block.appendChild(blockTitle);
          const list = document.createElement("ul");
          list.className = "simulator-derivation-list";
          if (values.length) {
            for (const value of values) {
              const li = document.createElement("li");
              li.textContent = String(value);
              list.appendChild(li);
            }
          } else {
            const li = document.createElement("li");
            li.textContent = "-";
            list.appendChild(li);
          }
          block.appendChild(list);
          detailBox.appendChild(block);
        }

        const impl = document.createElement("div");
        impl.className = "simulator-derivation-block";
        const implTitle = document.createElement("strong");
        implTitle.textContent = "Implemented in";
        const implValue = document.createElement("div");
        implValue.className = "simulator-derivation-impl";
        implValue.textContent = String(derivation.implemented_in || "-");
        impl.appendChild(implTitle);
        impl.appendChild(implValue);
        detailBox.appendChild(impl);
      });
      chip.appendChild(infoBtn);
    }
    host.appendChild(chip);
  }
}

function appendCapabilitySection(host, simulator) {
  const profileCapabilities = simulator.profile_capabilities && typeof simulator.profile_capabilities === "object"
    ? simulator.profile_capabilities
    : {};
  const profileIds = Object.keys(profileCapabilities);
  if (!profileIds.length) {
    return;
  }

  const section = document.createElement("section");
  section.className = "info-section";
  const title = document.createElement("h5");
  title.textContent = "Profile Capabilities";
  section.appendChild(title);

  const cards = document.createElement("div");
  cards.className = "simulator-capability-list";
  for (const profileId of profileIds) {
    const capability = profileCapabilities[profileId] || {};
    const derivations = profileDerivations(capability);
    const card = document.createElement("article");
    card.className = "simulator-capability-card";

    const header = document.createElement("div");
    header.className = "simulator-capability-head";
    const profileTitle = document.createElement("h6");
    profileTitle.textContent = profileId;
    header.appendChild(profileTitle);
    card.appendChild(header);

    const extrasRow = document.createElement("div");
    extrasRow.className = "simulator-capability-row";
    const extrasLabel = document.createElement("strong");
    extrasLabel.textContent = "Optional outputs";
    const extrasWrap = document.createElement("div");
    extrasWrap.className = "artifact-chip-row";
    const nativeExtras = Array.isArray(capability.native_extras) ? capability.native_extras : [];
    const derivableExtras = Array.isArray(capability.derivable_extras) ? capability.derivable_extras : [];
    appendArtifactChipRow(
      extrasWrap,
      [
        ...nativeExtras.map((artifact) => ({ artifact, mode: "native" })),
        ...derivableExtras.map((artifact) => ({ artifact, mode: "derivable" })),
      ],
      { derivations, simulator, profileId }
    );
    extrasRow.appendChild(extrasLabel);
    extrasRow.appendChild(extrasWrap);
    card.appendChild(extrasRow);

    const nativeOutputRow = document.createElement("div");
    nativeOutputRow.className = "simulator-capability-row";
    const nativeOutputLabel = document.createElement("strong");
    nativeOutputLabel.textContent = "Native outputs";
    const nativeOutputWrap = document.createElement("div");
    nativeOutputWrap.className = "artifact-chip-row";
    const nativeOutputs = Array.isArray(capability.native_outputs) ? capability.native_outputs : [];
    appendArtifactChipRow(
      nativeOutputWrap,
      nativeOutputs.map((item) => ({
        artifact: String(item?.id || "").trim(),
        label: String(item?.id || "").trim(),
        mode: "native",
      })),
      { derivations, simulator, profileId }
    );
    nativeOutputRow.appendChild(nativeOutputLabel);
    nativeOutputRow.appendChild(nativeOutputWrap);
    card.appendChild(nativeOutputRow);

    const truthRow = document.createElement("div");
    truthRow.className = "simulator-capability-row";
    const truthLabel = document.createElement("strong");
    truthLabel.textContent = "Truth outputs";
    const truthWrap = document.createElement("div");
    truthWrap.className = "artifact-chip-row";
    const truthEntries = Object.entries(capability.truth_outputs || {})
      .filter(([, mode]) => mode && mode !== "none")
      .map(([artifact, mode]) => ({ artifact, mode }));
    appendArtifactChipRow(truthWrap, truthEntries, { derivations, simulator, profileId });
    truthRow.appendChild(truthLabel);
    truthRow.appendChild(truthWrap);
    card.appendChild(truthRow);

    const detailBox = document.createElement("div");
    detailBox.className = "simulator-derivation-detail";
    detailBox.hidden = true;
    detailBox.dataset.artifact = "";
    card.appendChild(detailBox);

    cards.appendChild(card);
  }
  section.appendChild(cards);
  host.appendChild(section);
}

function showSimulatorInfo(simulator) {
  showInfoTooltip(simulatorInfoPayload(simulator));
  const content = $("info-popover-content");
  if (!content) {
    return;
  }
  appendCapabilitySection(content, simulator);
}

function populateSimulatorIssueSelect() {
  const select = $("simulator-issue-id");
  if (!select) {
    return;
  }
  select.innerHTML = "";
  for (const simulator of state.bootstrap?.simulators || []) {
    const option = document.createElement("option");
    option.value = simulator.simulator_id;
    option.textContent = simulator.name || simulator.simulator_id;
    select.appendChild(option);
  }
}

function openModal(id) {
  $(id)?.classList.remove("hidden");
}

function closeModal(id) {
  $(id)?.classList.add("hidden");
}

function buildSimulatorRequestIssueUrl() {
  const simulatorName = String($("simulator-request-name")?.value || "").trim();
  const doi = String($("simulator-request-doi")?.value || "").trim();
  const repoUrl = String($("simulator-request-repo")?.value || "").trim();
  const expectedProfiles = String($("simulator-request-profiles")?.value || "").trim();
  const expectedArtifacts = String($("simulator-request-artifacts")?.value || "").trim();
  const notes = String($("simulator-request-notes")?.value || "").trim();

  if (!simulatorName) {
    throw new Error("Simulator Name is required to create the issue.");
  }

  const params = new URLSearchParams();
  params.set("title", `[Simulator Request] ${simulatorName}`);
  params.set("labels", "simulator-request");
  params.set("body", [
    "## Simulator Request",
    "",
    `- Simulator name: ${simulatorName}`,
    `- DOI / publication: ${doi || "-"}`,
    `- Implementation repository: ${repoUrl || "-"}`,
    `- Expected canonical profiles: ${expectedProfiles || "-"}`,
    `- Expected extras / inputs: ${expectedArtifacts || "-"}`,
    "",
    "## Notes",
    notes || "-",
    "",
    "## Submitted From",
    "- GENECI GUI generate-data-v2",
  ].join("\n"));
  return `https://github.com/AdrianSeguraOrtiz/GENECI/issues/new?${params.toString()}`;
}

function buildSimulatorIssueReportUrl() {
  const simulatorId = String($("simulator-issue-id")?.value || "").trim();
  const issueType = String($("simulator-issue-type")?.value || "other").trim();
  const observed = String($("simulator-issue-observed")?.value || "").trim();
  const expected = String($("simulator-issue-expected")?.value || "").trim();
  const context = String($("simulator-issue-context")?.value || "").trim();

  if (!simulatorId) {
    throw new Error("Select a simulator to report.");
  }
  if (!observed) {
    throw new Error("Observed Behavior is required.");
  }

  const simulator = simulatorById(simulatorId);
  const simulatorName = String(simulator?.name || simulatorId);
  const params = new URLSearchParams();
  params.set("title", `[Simulator Catalog Issue] ${simulatorName} (${issueType})`);
  params.set("labels", "simulator-catalog-issue");
  params.set("body", [
    "## Simulator Catalog Issue",
    "",
    `- simulator_id: ${simulatorId}`,
    `- simulator_name: ${simulatorName}`,
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
    "- GENECI GUI generate-data-v2",
  ].join("\n"));
  return `https://github.com/AdrianSeguraOrtiz/GENECI/issues/new?${params.toString()}`;
}

function renderPreflightSummary(report) {
  const root = $("preflight-report-view");
  if (!report) {
    root.textContent = "No preflight report yet.";
    return;
  }
  const summary = report.catalog_summary || {};
  root.textContent = [
    `scenario: ${report.scenario?.id || "-"}`,
    `profile: ${report.scenario?.profile || "-"}`,
    `requested_extras: ${(report.scenario?.requested_extras || []).join(", ") || "(none)"}`,
    `effective_extras: ${(report.scenario?.effective_extras || []).join(", ") || "(none)"}`,
    `catalog: total=${summary.total ?? 0} eligible=${summary.eligible ?? 0} warning=${summary.warning ?? 0} blocked=${summary.blocked ?? 0}`,
  ].join("\n");
}

function simulatorMessages(entry) {
  return [...(entry.warnings || []), ...(entry.blocking_reasons || [])].filter(Boolean);
}

function renderSimulatorList(containerId, entries, kind) {
  const host = $(containerId);
  host.innerHTML = "";
  if (!entries.length) {
    const empty = document.createElement("div");
    empty.className = "muted-box";
    empty.textContent = "No simulators in this group.";
    host.appendChild(empty);
    return;
  }
  const template = $("simulator-catalog-item-template");
  for (const entry of entries) {
    const simulator = simulatorById(entry.simulator_id);
    if (!simulator) {
      continue;
    }
    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".tool-item-name").textContent = simulator.name;
    node.querySelector(".tool-item-badge").textContent = kind;
    node.querySelector(".tool-item-meta").textContent =
      `${simulator.first_author || "-"} ${simulator.year || ""} · ${entry.truth_outputs?.global_network || "truth?"} truth`;
    const actions = node.querySelector(".tool-item-actions");
    const infoBtn = document.createElement("button");
    infoBtn.type = "button";
    infoBtn.className = "secondary";
    infoBtn.textContent = "Simulator Info";
    infoBtn.addEventListener("click", () => showSimulatorInfo(simulator));
    actions.appendChild(infoBtn);
    if (kind !== "blocked") {
      const addBtn = document.createElement("button");
      addBtn.type = "button";
      addBtn.className = "secondary";
      addBtn.textContent = "Add Run";
      addBtn.addEventListener("click", () => {
        try {
          addRunCard({ simulator_id: simulator.simulator_id });
        } catch (err) {
          pushToast({ title: "Run configuration error", message: err.message, kind: "error", ttlMs: 8000 });
        }
      });
      actions.appendChild(addBtn);
    }
    const messages = simulatorMessages(entry);
    if (messages.length) {
      const detailsBtn = document.createElement("button");
      detailsBtn.type = "button";
      detailsBtn.className = "secondary";
      detailsBtn.textContent = kind === "blocked" ? "Why Blocked" : "View Details";
      detailsBtn.addEventListener("click", () =>
        showInfoTooltip({
          title: simulator.name,
          description: messages.join("\n"),
          example: "",
        })
      );
      actions.appendChild(detailsBtn);
    }
    host.appendChild(node);
  }
}

function renderSimulatorEligibility(report) {
  state.preflightReport = report;
  renderPreflightSummary(report);
  const eligible = Array.isArray(report?.eligible) ? report.eligible : [];
  const warning = Array.isArray(report?.warning) ? report.warning : [];
  const blocked = Array.isArray(report?.blocked) ? report.blocked : [];
  $("eligible-count").textContent = String(eligible.length);
  $("warning-count").textContent = String(warning.length);
  $("blocked-count").textContent = String(blocked.length);
  renderSimulatorList("simulators-eligible-list", eligible, "eligible");
  renderSimulatorList("simulators-warning-list", warning, "warning");
  renderSimulatorList("simulators-blocked-list", blocked, "blocked");
}

function availableSimulatorIds() {
  const report = state.preflightReport;
  if (!report) {
    return [];
  }
  return [...(report.eligible || []), ...(report.warning || [])]
    .map((entry) => String(entry.simulator_id || ""))
    .filter(Boolean);
}

function buildRunId(simulatorId) {
  const existing = Array.from(document.querySelectorAll(".run-id")).map((node) => node.value.trim());
  let idx = 1;
  while (existing.includes(`${simulatorId}__${String(idx).padStart(2, "0")}`)) {
    idx += 1;
  }
  return `${simulatorId}__${String(idx).padStart(2, "0")}`;
}

function updateRunParamsSummary(card, simulator, params = null) {
  const summary = card.querySelector(".run-params-summary");
  const current = params || readParamsFromHost(simulator, card.querySelector(".run-params-form"));
  summary.textContent = deepEqualJson(current, resolvedDefaultParams(simulator))
    ? "Default parameters"
    : "Custom parameters";
}

function renderCardParams(card, simulator, params = null) {
  const host = card.querySelector(".run-params-form");
  renderParamsHost(host, simulator, params, () => {
    refreshRunCardsValidation();
  });
  updateRunParamsSummary(card, simulator, readParamsFromHost(simulator, host));
}

function addRunCard(initial = {}) {
  const ids = availableSimulatorIds();
  if (!ids.length) {
    throw new Error("No eligible simulators available. Run preflight first.");
  }
  const simulatorId = initial.simulator_id || ids[0];
  const simulator = simulatorById(simulatorId);
  if (!simulator) {
    throw new Error(`Unknown simulator '${simulatorId}'`);
  }
  const node = $("run-template").content.firstElementChild.cloneNode(true);
  node.querySelector(".simulator-id").value = simulatorId;
  node.querySelector(".run-tool-name").textContent = simulator.name;
  node.querySelector(".run-id").value = initial.run_id || buildRunId(simulatorId);
  node.querySelector(".replicates").value = String(initial.replicates || 1);
  renderCardParams(node, simulator, initial.params || null);
  renderCardNativeOutputs(node, simulator, initial.native_outputs || []);
  node.querySelectorAll("input").forEach((input) => input.addEventListener("input", refreshRunCardsValidation));
  node.querySelector(".open-params").addEventListener("click", () => openParamsModal(node));
  node.querySelector(".reset-params").addEventListener("click", () => {
    renderCardParams(node, simulator, resolvedDefaultParams(simulator));
    renderCardNativeOutputs(node, simulator, []);
    refreshRunCardsValidation();
  });
  node.querySelector(".remove-run").addEventListener("click", () => {
    node.remove();
    updateRunsEmptyState();
    refreshRunCardsValidation();
    syncButtons();
  });
  $("runs-container").appendChild(node);
  updateRunsEmptyState();
  refreshRunCardsValidation();
  syncButtons();
}

function updateRunsEmptyState() {
  const hasRuns = Boolean(document.querySelectorAll(".run-card").length);
  $("runs-empty").style.display = hasRuns ? "none" : "block";
}

function refreshRunCardsValidation() {
  let ok = true;
  const seen = new Set();
  document.querySelectorAll(".run-card").forEach((card) => {
    const messages = [];
    const runId = card.querySelector(".run-id").value.trim();
    const replicates = Number.parseInt(card.querySelector(".replicates").value || "0", 10);
    if (!runId) {
      messages.push("Run ID is required.");
    } else if (seen.has(runId)) {
      messages.push(`Duplicate run_id: ${runId}`);
    }
    seen.add(runId);
    if (!Number.isInteger(replicates) || replicates < 1) {
      messages.push("Replicates must be >= 1.");
    }
    const simulator = simulatorById(card.querySelector(".simulator-id").value);
    try {
      readParamsFromHost(simulator, card.querySelector(".run-params-form"));
    } catch (err) {
      messages.push(String(err?.message || "Invalid parameters"));
    }
    const selectedNativeOutputs = readNativeOutputsFromHost(card.querySelector(".run-native-outputs-form"));
    const supportedNativeOutputs = new Set(nativeOutputDefsForSimulator(simulator).map((item) => String(item.id)));
    const unsupportedNativeOutputs = selectedNativeOutputs.filter((item) => !supportedNativeOutputs.has(String(item)));
    if (unsupportedNativeOutputs.length) {
      messages.push(`Unsupported native outputs: ${unsupportedNativeOutputs.join(", ")}`);
    }
    const validation = card.querySelector(".run-validation");
    validation.classList.toggle("ok", messages.length === 0);
    validation.classList.toggle("err", messages.length > 0);
    validation.textContent = messages.length ? messages.join("\n") : "Run configuration looks valid.";
    card.classList.toggle("invalid", messages.length > 0);
    if (messages.length) {
      ok = false;
    }
  });
  syncButtons();
  return ok;
}

function collectRuns() {
  const cards = Array.from(document.querySelectorAll(".run-card"));
  if (!cards.length) {
    throw new Error("At least one simulator run is required.");
  }
  if (!refreshRunCardsValidation()) {
    throw new Error("Fix invalid run configuration before planning.");
  }
  return cards.map((card) => {
    const simulator = simulatorById(card.querySelector(".simulator-id").value);
    return {
      run_id: card.querySelector(".run-id").value.trim(),
      simulator_id: simulator.simulator_id,
      replicates: Number.parseInt(card.querySelector(".replicates").value, 10),
      params: readParamsFromHost(simulator, card.querySelector(".run-params-form")),
      native_outputs: readNativeOutputsFromHost(card.querySelector(".run-native-outputs-form")),
    };
  });
}

function openParamsModal(card) {
  const simulator = simulatorById(card.querySelector(".simulator-id").value);
  const currentParams = readParamsFromHost(simulator, card.querySelector(".run-params-form"));
  const currentNativeOutputs = readNativeOutputsFromHost(card.querySelector(".run-native-outputs-form"));
  state.paramsModalCard = card;
  $("params-modal-title").textContent = `${simulator.name} · Configuration`;
  const status = $("params-modal-status");
  status.classList.remove("ok", "err");
  status.textContent = "Adjust native outputs and parameters, then apply changes.";
  renderParamsHost($("params-modal-form"), simulator, currentParams, () => {
    try {
      readParamsFromHost(simulator, $("params-modal-form"));
      status.classList.remove("ok", "err");
      status.textContent = "Adjust native outputs and parameters, then apply changes.";
    } catch (err) {
      status.classList.remove("ok");
      status.classList.add("err");
      status.textContent = String(err?.message || "Invalid parameter value");
    }
  });
  renderNativeOutputsHost($("params-modal-native-outputs"), simulator, currentNativeOutputs);
  $("params-modal").classList.remove("hidden");
}

function closeParamsModal() {
  $("params-modal").classList.add("hidden");
  $("params-modal-form").innerHTML = "";
  $("params-modal-native-outputs").innerHTML = "";
  $("params-modal-title").textContent = "Configuration";
  $("params-modal-status").classList.remove("ok", "err");
  $("params-modal-status").textContent = "Adjust native outputs and parameters, then apply changes.";
  state.paramsModalCard = null;
}

function applyParamsModal() {
  if (!state.paramsModalCard) {
    closeParamsModal();
    return;
  }
  const simulator = simulatorById(state.paramsModalCard.querySelector(".simulator-id").value);
  try {
    const params = readParamsFromHost(simulator, $("params-modal-form"));
    const nativeOutputs = readNativeOutputsFromHost($("params-modal-native-outputs"));
    renderCardParams(state.paramsModalCard, simulator, params);
    renderCardNativeOutputs(state.paramsModalCard, simulator, nativeOutputs);
    refreshRunCardsValidation();
    closeParamsModal();
  } catch (err) {
    $("params-modal-status").classList.remove("ok");
    $("params-modal-status").classList.add("err");
    $("params-modal-status").textContent = String(err?.message || "Invalid parameters");
  }
}

function renderPlan(plan) {
  const summary = $("plan-summary");
  const tables = $("plan-tables");
  tables.innerHTML = "";
  if (!plan || typeof plan !== "object") {
    summary.textContent = "No plan loaded yet.";
    return;
  }
  summary.textContent = [
    `benchmark: ${plan.id || "-"}`,
    `profile: ${plan.profile || "-"}`,
    `runs: ${(plan.runs || []).length}`,
    `tasks: ${(plan.tasks || []).length}`,
    `max_parallel_tasks: ${plan.execution?.max_parallel_tasks ?? "-"}`,
  ].join("\n");

  const runsCard = document.createElement("article");
  runsCard.className = "wave-card";
  runsCard.innerHTML = "<h3>Simulator Runs</h3>";
  const runsTable = document.createElement("table");
  runsTable.className = "wave-table";
  runsTable.innerHTML = "<thead><tr><th>run_id</th><th>simulator</th><th>replicates</th><th>native_outputs</th><th>base_seed</th><th>replicate_seeds</th></tr></thead>";
  const runsBody = document.createElement("tbody");
  for (const run of plan.runs || []) {
    const tr = document.createElement("tr");
    [
      run.run_id,
      run.simulator_id,
      run.replicates,
      (run.native_outputs || []).join(", ") || "-",
      run.base_seed,
      (run.replicate_seeds || []).join(", "),
    ].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = String(value ?? "-");
      tr.appendChild(td);
    });
    runsBody.appendChild(tr);
  }
  runsTable.appendChild(runsBody);
  runsCard.appendChild(runsTable);
  tables.appendChild(runsCard);

  const tasksCard = document.createElement("article");
  tasksCard.className = "wave-card";
  tasksCard.innerHTML = "<h3>Planned Tasks</h3>";
  const tasksTable = document.createElement("table");
  tasksTable.className = "wave-table";
  tasksTable.innerHTML = "<thead><tr><th>task_id</th><th>run_id</th><th>replicate</th><th>seed</th><th>dataset_id</th></tr></thead>";
  const tasksBody = document.createElement("tbody");
  for (const task of plan.tasks || []) {
    const tr = document.createElement("tr");
    [task.task_id, task.run_id, task.replicate_index, task.seed, task.dataset_id].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = String(value ?? "-");
      tr.appendChild(td);
    });
    tasksBody.appendChild(tr);
  }
  tasksTable.appendChild(tasksBody);
  tasksCard.appendChild(tasksTable);
  tables.appendChild(tasksCard);
}

function renderExecutionAlerts(job) {
  const root = $("execution-alerts");
  const error = String(job?.error || "").trim();
  if (!error) {
    root.textContent = "No execution errors or warnings.";
    return;
  }
  root.textContent = error;
  pushToast({ title: "Job failed", message: error, kind: "error", ttlMs: 9000 });
}

function hasExecutionArtifacts(job) {
  return Boolean(job?.benchmark_root) && (job.stage === "executed" || job.status === "failed");
}

function updateExplorerVisibility(job) {
  const visible = hasExecutionArtifacts(job);
  $("results-explorer-section").hidden = !visible;
  $("results-explorer-placeholder").hidden = visible;
  if (!visible) {
    resetFilesView(state, "Results Explorer will be available after execution.");
    resetReproducibility("Reproducibility snippets will be available after execution.");
  }
}

async function refreshFilesIfNeeded(job) {
  if (!hasExecutionArtifacts(job)) {
    return;
  }
  const key = `${job.job_id}:${$("bundle-mode").value}:${job.status}:${job.benchmark_root}`;
  if (state.loadedFilesKey === key) {
    return;
  }
  await fetchFiles(state, fileApi(), {}, fileExplorerOptions());
  state.loadedFilesKey = key;
}

function syncButtons() {
  const job = state.currentJob;
  const busy = job?.status === "queued" || job?.status === "running";
  const preflightReady = ["preflight_ok", "planned", "executed"].includes(job?.stage || "");
  const planReady = ["planned", "executed"].includes(job?.stage || "");
  const executed = job?.stage === "executed";
  const hasRuns = Boolean(document.querySelectorAll(".run-card").length);
  $("preflight-btn").disabled = busy;
  $("step-1-next-btn").disabled = busy || !preflightReady;
  $("add-all-simulators-btn").disabled = busy || !preflightReady || availableSimulatorIds().length === 0;
  $("clear-runs-btn").disabled = busy || !hasRuns;
  $("plan-btn").disabled = busy || !preflightReady || !hasRuns;
  $("step-2-next-btn").disabled = busy || !planReady;
  $("execute-btn").disabled = busy || !planReady || executed;
  setStepState(1, preflightReady ? "ready" : busy ? "running" : "draft");
  setStepState(2, planReady ? "ready" : preflightReady ? "ready" : "blocked");
  setStepState(3, executed ? "ready" : planReady ? "ready" : "blocked");
}

async function pollJob(jobId) {
  const payload = await fetchJob(jobId);
  const job = payload.job;
  state.currentJob = job;
  if (payload.preflight_report) {
    renderSimulatorEligibility(payload.preflight_report);
  }
  if (payload.plan) {
    renderPlan(payload.plan);
  } else if (job.plan_path) {
    const planPayload = await fetchPlan(job.job_id);
    renderPlan(planPayload.plan);
  }
  renderRuntimeProgress(payload.runtime_progress);
  pushRuntimeFailureToasts(payload.runtime_progress, state.notifiedFailures);
  renderExecutionAlerts(job);
  renderReproducibility(payload.reproducibility);
  updateExplorerVisibility(job);
  await refreshFilesIfNeeded(job);
  if (job.status === "running" && job.stage === "planned") {
    setActiveStep(3, { scroll: false });
  }
  syncButtons();
  if (job.status === "completed" || job.status === "failed") {
    if (state.pollTimer) {
      window.clearInterval(state.pollTimer);
      state.pollTimer = null;
    }
  }
}

async function startPolling(jobId) {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
  }
  await pollJob(jobId);
  state.pollTimer = window.setInterval(() => {
    pollJob(jobId).catch((err) => pushToast({ title: "Polling error", message: err.message, kind: "error" }));
  }, 1500);
}

async function handlePreflight() {
  try {
    const payload = await submitPreflight(buildPreflightFormData());
    state.jobId = payload.job_id;
    state.currentJob = { job_id: payload.job_id, status: "queued", stage: "draft" };
    renderPlan(null);
    $("runs-container").innerHTML = "";
    updateRunsEmptyState();
    syncButtons();
    await startPolling(payload.job_id);
  } catch (err) {
    pushToast({ title: "Preflight failed", message: err.message, kind: "error" });
  }
}

async function handlePlan() {
  try {
    const payload = await submitPlan({
      job_id: state.jobId,
      runs: collectRuns(),
      options: {
        max_parallel_tasks: Number.parseInt($("max-parallel-tasks").value || "1", 10),
        output_dir: $("output-dir").value.trim() || "./benchmarks_v2",
      },
    });
    await startPolling(payload.job_id);
  } catch (err) {
    pushToast({ title: "Plan failed", message: err.message, kind: "error" });
  }
}

async function handleRun() {
  try {
    const payload = await submitRun({
      job_id: state.jobId,
      options: {
        max_parallel_tasks: Number.parseInt($("max-parallel-tasks").value || "1", 10),
        output_dir: $("output-dir").value.trim() || "./benchmarks_v2",
        progress_poll_seconds: Number($("progress-poll").value || 0.5),
      },
    });
    setActiveStep(3);
    await startPolling(payload.job_id);
  } catch (err) {
    pushToast({ title: "Run failed", message: err.message, kind: "error" });
  }
}

function initEvents() {
  $("add-input-btn").addEventListener("click", addInputRow);
  $("preflight-btn").addEventListener("click", handlePreflight);
  $("plan-btn").addEventListener("click", handlePlan);
  $("execute-btn").addEventListener("click", handleRun);
  $("step-1-next-btn").addEventListener("click", () => setActiveStep(2));
  $("step-2-next-btn").addEventListener("click", () => setActiveStep(3));
  $("add-all-simulators-btn").addEventListener("click", () => {
    try {
      for (const simulatorId of availableSimulatorIds()) {
        addRunCard({ simulator_id: simulatorId });
      }
    } catch (err) {
      pushToast({ title: "Run configuration error", message: err.message, kind: "error", ttlMs: 8000 });
    }
  });
  $("clear-runs-btn").addEventListener("click", () => {
    $("runs-container").innerHTML = "";
    updateRunsEmptyState();
    refreshRunCardsValidation();
    syncButtons();
  });
  $("open-simulator-request-modal-btn").addEventListener("click", () => openModal("simulator-request-modal"));
  $("open-simulator-issue-modal-btn").addEventListener("click", () => openModal("simulator-issue-modal"));
  $("simulator-request-modal-close").addEventListener("click", () => closeModal("simulator-request-modal"));
  $("simulator-issue-modal-close").addEventListener("click", () => closeModal("simulator-issue-modal"));
  $("simulator-request-modal").addEventListener("click", (event) => {
    if (event.target && event.target.id === "simulator-request-modal") {
      closeModal("simulator-request-modal");
    }
  });
  $("simulator-issue-modal").addEventListener("click", (event) => {
    if (event.target && event.target.id === "simulator-issue-modal") {
      closeModal("simulator-issue-modal");
    }
  });
  $("open-simulator-request-issue-btn").addEventListener("click", () => {
    try {
      window.open(buildSimulatorRequestIssueUrl(), "_blank", "noopener");
      closeModal("simulator-request-modal");
      pushToast({
        title: "GitHub issue opened",
        message: "Opened prefilled simulator request in a new tab.",
        kind: "success",
        ttlMs: 4500,
      });
    } catch (err) {
      pushToast({ title: "Simulator request error", message: err.message, kind: "error", ttlMs: 7000 });
    }
  });
  $("open-simulator-issue-btn").addEventListener("click", () => {
    try {
      window.open(buildSimulatorIssueReportUrl(), "_blank", "noopener");
      closeModal("simulator-issue-modal");
      pushToast({
        title: "GitHub issue opened",
        message: "Opened prefilled simulator issue in a new tab.",
        kind: "success",
        ttlMs: 4500,
      });
    } catch (err) {
      pushToast({ title: "Simulator issue error", message: err.message, kind: "error", ttlMs: 7000 });
    }
  });
  $("params-modal-close").addEventListener("click", closeParamsModal);
  $("params-modal-save").addEventListener("click", applyParamsModal);
  $("params-modal-reset").addEventListener("click", () => {
    if (!state.paramsModalCard) {
      return;
    }
    const simulator = simulatorById(state.paramsModalCard.querySelector(".simulator-id").value);
    renderParamsHost($("params-modal-form"), simulator, resolvedDefaultParams(simulator));
    renderNativeOutputsHost($("params-modal-native-outputs"), simulator, []);
    $("params-modal-status").classList.remove("ok", "err");
    $("params-modal-status").textContent = "Default parameters restored and native outputs cleared in the modal. Apply to save them.";
  });
  $("params-modal").addEventListener("click", (event) => {
    if (event.target && event.target.id === "params-modal") {
      closeParamsModal();
    }
  });
  $("refresh-files-btn").addEventListener("click", () => fetchFiles(state, fileApi(), {}, fileExplorerOptions()).catch((err) => {
    pushToast({ title: "Files error", message: err.message, kind: "error" });
  }));
  $("bundle-mode").addEventListener("change", () => {
    state.loadedFilesKey = null;
    if (state.currentJob) {
      refreshFilesIfNeeded(state.currentJob).catch((err) => pushToast({ title: "Files error", message: err.message, kind: "error" }));
    }
  });
  $("download-bundle-btn").addEventListener("click", () => {
    if (!state.jobId) {
      return;
    }
    window.location.href = `/api/generate-data-v2/jobs/${state.jobId}/bundle?mode=${encodeURIComponent($("bundle-mode").value)}`;
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    closeParamsModal();
    closeModal("simulator-request-modal");
    closeModal("simulator-issue-modal");
  });
}

async function main() {
  initSteps(3);
  initInfoPopover();
  initReproducibility();
  initEvents();
  state.bootstrap = await fetchBootstrapData();
  state.simulatorsById = new Map((state.bootstrap.simulators || []).map((item) => [item.simulator_id, item]));
  initBootstrapView();
  updateInputsEmptyState();
  updateRunsEmptyState();
  syncButtons();
}

main().catch((err) => {
  pushToast({ title: "Startup failed", message: err.message, kind: "error", ttlMs: 10000 });
});
