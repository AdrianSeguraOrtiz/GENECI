import { state } from "../core/state.js";

export function getExpressionHelp() {
  const help = state.bootstrap?.dataset_input_help?.expression_matrix || {};
  return {
    description: String(help.description || "").trim(),
    example: String(help.example || "").trim(),
    file_kind: String(help.file_kind || "tsv"),
    delimiter: String(help.delimiter || "\t"),
    header: Boolean(help.header ?? true),
    min_rows: Number.isFinite(Number(help.min_rows)) ? Number(help.min_rows) : 1,
    min_columns: Number.isFinite(Number(help.min_columns)) ? Number(help.min_columns) : 2,
    required_columns: Array.isArray(help.required_columns) ? help.required_columns : [],
    column_types: help.column_types && typeof help.column_types === "object" ? help.column_types : {},
    first_column_role: String(help.first_column_role || "none"),
    first_column_disallowed_names: Array.isArray(help.first_column_disallowed_names)
      ? help.first_column_disallowed_names
      : [],
    unique_first_column: Boolean(help.unique_first_column ?? false),
    data_columns_type: String(help.data_columns_type || "any"),
    data_numeric_min_fraction: Number.isFinite(Number(help.data_numeric_min_fraction))
      ? Number(help.data_numeric_min_fraction)
      : 1.0,
  };
}

export function getExtraMeta(key) {
  const list = Array.isArray(state.bootstrap?.extra_inputs) ? state.bootstrap.extra_inputs : [];
  return list.find((item) => item.key === key) || null;
}

export function setStatusBadge(el, kind, text) {
  if (!el) {
    return;
  }
  el.classList.remove("ok", "err");
  if (kind === "ok") {
    el.classList.add("ok");
  } else if (kind === "err") {
    el.classList.add("err");
  }
  el.textContent = text;
}

function tabularValidationMeta(meta = {}, defaults = {}) {
  const merged = { ...defaults, ...(meta && typeof meta === "object" ? meta : {}) };
  return {
    delimiter: String(merged.delimiter || "\t"),
    hasHeader: Boolean(merged.header ?? true),
    minRows: Number.isFinite(Number(merged.min_rows)) ? Number(merged.min_rows) : 1,
    minColumns: Number.isFinite(Number(merged.min_columns)) ? Number(merged.min_columns) : 1,
    requiredColumns: Array.isArray(merged.required_columns) ? merged.required_columns : [],
    columnTypes: merged.column_types && typeof merged.column_types === "object" ? merged.column_types : {},
    firstColumnRole: String(merged.first_column_role || "none"),
    disallowedFirstHeader: new Set(
      (Array.isArray(merged.first_column_disallowed_names) ? merged.first_column_disallowed_names : [])
        .map((x) => String(x || "").trim().toLowerCase())
        .filter(Boolean)
    ),
    uniqueFirstColumn: Boolean(merged.unique_first_column ?? false),
    dataColumnsType: String(merged.data_columns_type || "any"),
    dataNumericMinFraction: Number.isFinite(Number(merged.data_numeric_min_fraction))
      ? Math.max(0, Math.min(1, Number(merged.data_numeric_min_fraction)))
      : 1.0,
  };
}

function validateTabularContent(
  raw,
  spec,
  {
    invalidFirstHeaderMessage = (header) => `first column header '${header}' is not valid for this input`,
    emptyFirstValueMessage = (line) => `empty first-column identifier at line ${line}`,
    duplicatedFirstValueMessage = (value, line) => `duplicated first-column identifier '${value}' at line ${line}`,
  } = {}
) {
  const lines = raw.split(/\r?\n/).filter((line) => line.length > 0);
  if (!lines.length) {
    throw new Error("empty file");
  }

  const split = (line) => line.split(spec.delimiter);
  const header = spec.hasHeader ? split(lines[0]) : [];
  if (spec.hasHeader && header.length < 1) {
    throw new Error("invalid header");
  }
  const expectedCols = spec.hasHeader ? header.length : split(lines[0]).length;
  if (expectedCols < spec.minColumns) {
    throw new Error(`expected at least ${spec.minColumns} columns, got ${expectedCols}`);
  }
  if (spec.hasHeader) {
    const headerSet = new Set(header.map((x) => String(x || "").trim()));
    const missing = spec.requiredColumns.filter((col) => !headerSet.has(String(col)));
    if (missing.length) {
      throw new Error(`missing required column(s): ${missing.join(", ")}`);
    }
    if (spec.firstColumnRole === "gene_id") {
      const firstHeader = String(header[0] || "").trim().toLowerCase();
      if (!firstHeader) {
        throw new Error("first column header cannot be empty");
      }
      if (spec.disallowedFirstHeader.has(firstHeader)) {
        throw new Error(invalidFirstHeaderMessage(header[0]));
      }
    }
  } else if (spec.requiredColumns.length) {
    throw new Error("missing required column(s): header is required");
  }

  const firstSeen = new Set();
  let dataCellsTotal = 0;
  let dataCellsNumeric = 0;
  let rows = 0;
  const start = spec.hasHeader ? 1 : 0;
  for (let idx = start; idx < lines.length; idx += 1) {
    const cols = split(lines[idx]);
    if (cols.length !== expectedCols) {
      throw new Error(`inconsistent number of columns at line ${idx + 1}`);
    }
    if (spec.firstColumnRole === "gene_id") {
      const firstValue = String(cols[0] || "").trim();
      if (!firstValue) {
        throw new Error(emptyFirstValueMessage(idx + 1));
      }
      if (spec.uniqueFirstColumn && firstSeen.has(firstValue)) {
        throw new Error(duplicatedFirstValueMessage(firstValue, idx + 1));
      }
      firstSeen.add(firstValue);
    }
    if (spec.dataColumnsType === "float" && cols.length > 1) {
      for (const valueRaw of cols.slice(1)) {
        const value = String(valueRaw || "").trim();
        dataCellsTotal += 1;
        if (value && !Number.isNaN(Number(value))) {
          dataCellsNumeric += 1;
        }
      }
    }
    if (spec.hasHeader) {
      for (const [colName, typeName] of Object.entries(spec.columnTypes)) {
        const colIdx = header.findIndex((x) => String(x || "").trim() === colName);
        if (colIdx < 0) {
          continue;
        }
        const cell = String(cols[colIdx] || "").trim();
        if (!cell) {
          continue;
        }
        if (typeName === "int" && !/^-?\d+$/.test(cell)) {
          throw new Error(`column '${colName}' must be int (line ${idx + 1})`);
        }
        if (typeName === "float" && Number.isNaN(Number(cell))) {
          throw new Error(`column '${colName}' must be float (line ${idx + 1})`);
        }
        if (typeName === "bool" && !["true", "false", "1", "0"].includes(cell.toLowerCase())) {
          throw new Error(`column '${colName}' must be bool (line ${idx + 1})`);
        }
      }
    }
    rows += 1;
  }
  if (rows < spec.minRows) {
    throw new Error(`expected at least ${spec.minRows} row(s), got ${rows}`);
  }
  if (spec.dataColumnsType === "float" && dataCellsTotal > 0) {
    const ratio = dataCellsNumeric / dataCellsTotal;
    if (ratio < spec.dataNumericMinFraction) {
      throw new Error(
        `only ${(ratio * 100).toFixed(1)}% numeric values in data columns (required >= ${(spec.dataNumericMinFraction * 100).toFixed(1)}%)`
      );
    }
  }
  return { rows, columns: expectedCols };
}

export async function validateExpressionFile(file) {
  const raw = await file.text();
  const spec = tabularValidationMeta(getExpressionHelp(), { min_rows: 1, min_columns: 2 });
  const inspected = validateTabularContent(raw, spec, {
    invalidFirstHeaderMessage: (header) =>
      `first column header '${header}' is not valid for expression genes`,
    emptyFirstValueMessage: (line) => `empty gene identifier at line ${line}`,
    duplicatedFirstValueMessage: (value, line) => `duplicated gene identifier '${value}' at line ${line}`,
  });
  if (inspected.rows < 1) {
    throw new Error("no gene rows found");
  }
  return { genes: inspected.rows, columns: inspected.columns - 1 };
}

export async function validateOptionalFile(file, key) {
  const ext = file.name.includes(".") ? file.name.split(".").pop().toLowerCase() : "";
  const meta = getExtraMeta(key);
  const defaultName = String(meta?.default_filename || "");
  const expectedExt = defaultName.includes(".") ? defaultName.split(".").pop().toLowerCase() : "";
  if (expectedExt && ext && ext !== expectedExt) {
    throw new Error(`expected .${expectedExt} file, got .${ext}`);
  }

  const raw = await file.text();
  const lines = raw.split(/\r?\n/).filter((line) => line.length > 0);
  if (!lines.length) {
    throw new Error("empty file");
  }

  const fileKind = String(meta?.file_kind || "").trim() || "tsv";
  const minRows = Number.isFinite(Number(meta?.min_rows)) ? Number(meta?.min_rows) : 0;
  if (fileKind === "txt_list") {
    if (lines.length < minRows) {
      throw new Error(`expected at least ${minRows} non-empty line(s), got ${lines.length}`);
    }
    return { rows: lines.length, columns: 1 };
  }

  const spec = tabularValidationMeta(meta, { min_rows: 0, min_columns: 1 });
  const inspected = validateTabularContent(raw, spec, {
    invalidFirstHeaderMessage: (header) =>
      `first column header '${header}' is not valid for this input`,
    emptyFirstValueMessage: (line) => `empty first-column identifier at line ${line}`,
    duplicatedFirstValueMessage: (value, line) =>
      `duplicated first-column identifier '${value}' at line ${line}`,
  });
  return { rows: inspected.rows, columns: inspected.columns };
}
