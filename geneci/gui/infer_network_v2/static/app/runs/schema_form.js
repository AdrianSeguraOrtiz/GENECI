import { buildInfoTooltip, readHelpPayload, showInfoTooltip } from "../ui/popovers.js";

export function deepClone(value) {
  return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function valueAtPath(payload, rawPath) {
  const path = String(rawPath || "").trim();
  if (!path) {
    return undefined;
  }
  const parts = path.split(".").map((item) => item.trim()).filter(Boolean);
  let current = payload;
  for (const part of parts) {
    if (!current || typeof current !== "object" || !(part in current)) {
      return undefined;
    }
    current = current[part];
  }
  return current;
}

function matchesCondition(actual, op, expected) {
  if (op === "eq") {
    return actual === expected;
  }
  if (op === "ne") {
    return actual !== expected;
  }
  if (
    typeof actual === "boolean" ||
    typeof expected === "boolean" ||
    Number.isNaN(Number(actual)) ||
    Number.isNaN(Number(expected))
  ) {
    return false;
  }
  const actualNum = Number(actual);
  const expectedNum = Number(expected);
  if (op === "gt") {
    return actualNum > expectedNum;
  }
  if (op === "gte") {
    return actualNum >= expectedNum;
  }
  if (op === "lt") {
    return actualNum < expectedNum;
  }
  if (op === "lte") {
    return actualNum <= expectedNum;
  }
  return false;
}

export function conditionalRuleMatches(params, rule) {
  const actual = valueAtPath(params, rule?.param);
  return matchesCondition(actual, String(rule?.op || "").trim(), rule?.value);
}

function isNullSchemaVariant(schema) {
  if (!schema || typeof schema !== "object") {
    return false;
  }
  return String(schema.type || "").trim() === "object" && !schema.properties && schema.default === null;
}

function matchesSchemaValue(value, schema) {
  const type = String(schema?.type || "").trim();
  if (isNullSchemaVariant(schema)) {
    return value === null;
  }
  if (type === "int") {
    return Number.isInteger(value);
  }
  if (type === "float") {
    return typeof value === "number" && Number.isFinite(value);
  }
  if (type === "bool") {
    return typeof value === "boolean";
  }
  if (type === "string") {
    return typeof value === "string";
  }
  if (type === "enum") {
    return typeof value === "string";
  }
  if (type === "object") {
    return value && typeof value === "object" && !Array.isArray(value);
  }
  if (type === "union") {
    const variants = Array.isArray(schema?.oneOf) ? schema.oneOf : [];
    return variants.some((item) => matchesSchemaValue(value, item));
  }
  return false;
}

export function defaultForSchema(schema) {
  if (schema && Object.prototype.hasOwnProperty.call(schema, "default")) {
    return deepClone(schema.default);
  }
  const type = String(schema?.type || "").trim();
  if (type === "object") {
    const out = {};
    const props = schema?.properties && typeof schema.properties === "object" ? schema.properties : {};
    for (const [key, child] of Object.entries(props)) {
      out[key] = defaultForSchema(child);
    }
    return out;
  }
  if (type === "bool") {
    return false;
  }
  if (type === "int" || type === "float") {
    return 0;
  }
  if (type === "string" || type === "enum") {
    return "";
  }
  return null;
}

export function resolvedDefaultParams(tool) {
  const schemaMap = tool?.params_schema && typeof tool.params_schema === "object" ? tool.params_schema : {};
  const out = {};
  for (const [key, schema] of Object.entries(schemaMap)) {
    out[key] = defaultForSchema(schema);
  }
  return out;
}

function defaultUnionVariantIndex(schema, value) {
  const variants = Array.isArray(schema?.oneOf) ? schema.oneOf : [];
  const matchIndex = variants.findIndex((variant) => matchesSchemaValue(value, variant));
  if (matchIndex >= 0) {
    return matchIndex;
  }
  const nullIndex = variants.findIndex((variant) => isNullSchemaVariant(variant));
  return nullIndex >= 0 ? nullIndex : 0;
}

function unionVariantLabel(schema, index) {
  const type = String(schema?.type || "").trim();
  if (isNullSchemaVariant(schema)) {
    return "null";
  }
  if (type === "enum") {
    return `enum ${index + 1}`;
  }
  if (type === "object") {
    return "object";
  }
  return type || `option ${index + 1}`;
}

function paramDescriptionPayload(label, schema) {
  const type = String(schema?.type || "").trim() || "unknown";
  const bits = [`Type: ${type}`];
  if (Array.isArray(schema?.enum) && schema.enum.length) {
    bits.push(`Allowed values: ${schema.enum.join(", ")}`);
  }
  if (schema?.min !== undefined) {
    bits.push(`${schema.exclusive_min ? "Exclusive min" : "Min"}: ${schema.min}`);
  }
  if (schema?.max !== undefined) {
    bits.push(`${schema.exclusive_max ? "Exclusive max" : "Max"}: ${schema.max}`);
  }
  if (Object.prototype.hasOwnProperty.call(schema || {}, "default")) {
    bits.push(`Default: ${JSON.stringify(schema.default)}`);
  }
  return buildInfoTooltip({
    title: label,
    description: [String(schema?.description || "").trim(), bits.join(" | ")]
      .filter(Boolean)
      .join("\n"),
    example: "",
  });
}

export function setParamFieldError(field, message = "") {
  if (!field) {
    return;
  }
  field.classList.toggle("invalid", Boolean(message));
  let errorEl = field.querySelector(".param-error");
  if (!errorEl) {
    errorEl = document.createElement("div");
    errorEl.className = "param-error";
    field.appendChild(errorEl);
  }
  errorEl.textContent = String(message || "").trim();
}

function createParamFieldShell({ key, schema }) {
  const field = document.createElement("section");
  field.className = "param-field";
  field.dataset.paramKey = key;
  field.dataset.paramType = String(schema?.type || "").trim();

  const head = document.createElement("div");
  head.className = "param-field-head";

  const titleWrap = document.createElement("div");
  titleWrap.className = "param-field-title";

  const nameEl = document.createElement("div");
  nameEl.className = "param-field-name";
  nameEl.textContent = key;
  titleWrap.appendChild(nameEl);

  const metaBits = [];
  if (schema?.required) {
    metaBits.push("required");
  }
  if (metaBits.length) {
    const meta = document.createElement("div");
    meta.className = "param-field-meta";
    meta.textContent = metaBits.join(" · ");
    titleWrap.appendChild(meta);
  }

  const infoBtn = document.createElement("button");
  infoBtn.type = "button";
  infoBtn.className = "info-icon";
  infoBtn.title = "Parameter info";
  infoBtn.setAttribute("aria-label", `${key} info`);
  infoBtn.textContent = "i";
  infoBtn.dataset.help = JSON.stringify(paramDescriptionPayload(key, schema));
  infoBtn.addEventListener("click", () => {
    const payload = readHelpPayload(infoBtn);
    if (payload) {
      showInfoTooltip(payload);
    }
  });

  head.appendChild(titleWrap);
  head.appendChild(infoBtn);
  field.appendChild(head);
  return field;
}

function renderPrimitiveEditor(field, schema, value) {
  const wrap = document.createElement("div");
  wrap.className = "param-input-wrap";
  const type = String(schema?.type || "").trim();
  let input = null;

  if (type === "bool") {
    input = document.createElement("select");
    input.className = "param-input";
    input.dataset.inputKind = "bool";
    [
      { value: "true", label: "true" },
      { value: "false", label: "false" },
    ].forEach((item) => {
      const option = document.createElement("option");
      option.value = item.value;
      option.textContent = item.label;
      input.appendChild(option);
    });
    input.value = String(Boolean(value));
  } else if (type === "enum") {
    input = document.createElement("select");
    input.className = "param-input";
    input.dataset.inputKind = "enum";
    const values = Array.isArray(schema?.enum) ? schema.enum : [];
    for (const item of values) {
      const option = document.createElement("option");
      option.value = String(item);
      option.textContent = String(item);
      input.appendChild(option);
    }
    input.value = values.includes(value) ? String(value) : String(values[0] ?? "");
  } else if (type === "int" || type === "float") {
    input = document.createElement("input");
    input.type = "number";
    input.className = "param-input";
    input.dataset.inputKind = type;
    input.step = type === "int" ? "1" : "any";
    if (schema?.min !== undefined) {
      input.min = String(schema.min);
    }
    if (schema?.max !== undefined) {
      input.max = String(schema.max);
    }
    input.value = value === null || value === undefined ? "" : String(value);
  } else {
    input = document.createElement("input");
    input.type = "text";
    input.className = "param-input";
    input.dataset.inputKind = "string";
    input.value = value === null || value === undefined ? "" : String(value);
  }

  wrap.appendChild(input);
  field.appendChild(wrap);
}

function bindInputListeners(root, onChange) {
  if (typeof onChange !== "function") {
    return;
  }
  root.querySelectorAll("input, select, textarea").forEach((input) => {
    input.addEventListener("input", onChange);
    input.addEventListener("change", onChange);
  });
}

function renderParamField(field, schema, value, onChange) {
  const type = String(schema?.type || "").trim();

  if (type === "object") {
    const childWrap = document.createElement("div");
    childWrap.className = "param-object-fields";
    const props = schema?.properties && typeof schema.properties === "object" ? schema.properties : {};
    const currentValue = value && typeof value === "object" && !Array.isArray(value) ? value : {};
    for (const [childKey, childSchema] of Object.entries(props)) {
      const childField = createParamFieldShell({
        key: childKey,
        schema: childSchema,
      });
      renderParamField(childField, childSchema, currentValue[childKey], onChange);
      childWrap.appendChild(childField);
    }
    field.appendChild(childWrap);
    return;
  }

  if (type === "union") {
    const variants = Array.isArray(schema?.oneOf) ? schema.oneOf : [];
    const currentIndex = defaultUnionVariantIndex(schema, value);
    field.dataset.unionVariantIndex = String(currentIndex);

    const head = document.createElement("div");
    head.className = "param-union-head";
    const selector = document.createElement("select");
    selector.className = "param-input";
    selector.dataset.inputKind = "union-variant";
    variants.forEach((variant, idx) => {
      const option = document.createElement("option");
      option.value = String(idx);
      option.textContent = unionVariantLabel(variant, idx);
      selector.appendChild(option);
    });
    selector.value = String(currentIndex);
    head.appendChild(selector);
    field.appendChild(head);

    const body = document.createElement("div");
    body.className = "param-object-fields";
    body.dataset.unionBody = "true";
    field.appendChild(body);

    const renderVariant = () => {
      body.innerHTML = "";
      field.dataset.unionVariantIndex = selector.value;
      const index = Number(selector.value);
      const variant = variants[index];
      if (isNullSchemaVariant(variant)) {
        const note = document.createElement("div");
        note.className = "muted-box";
        note.textContent = "Value: null";
        body.appendChild(note);
        return;
      }
      const variantField = createParamFieldShell({
        key: `${field.dataset.paramKey} value`,
        schema: variant,
      });
      renderParamField(
        variantField,
        variant,
        matchesSchemaValue(value, variant) ? value : defaultForSchema(variant),
        onChange
      );
      body.appendChild(variantField);
      bindInputListeners(body, onChange);
    };

    selector.addEventListener("change", () => {
      value = defaultForSchema(variants[Number(selector.value)]);
      renderVariant();
      if (typeof onChange === "function") {
        onChange();
      }
    });

    renderVariant();
    return;
  }

  renderPrimitiveEditor(field, schema, value);
}

function readParamFieldValue(field, schema, label) {
  const type = String(schema?.type || "").trim();

  if (type === "object") {
    const out = {};
    const props = schema?.properties && typeof schema.properties === "object" ? schema.properties : {};
    for (const [key, childSchema] of Object.entries(props)) {
      const childField = field.querySelector(
        `:scope > .param-object-fields > .param-field[data-param-key="${CSS.escape(key)}"]`
      );
      if (!childField) {
        throw new Error(`${label}.${key}: field is missing`);
      }
      out[key] = readParamFieldValue(childField, childSchema, `${label}.${key}`);
    }
    return out;
  }

  if (type === "union") {
    const variants = Array.isArray(schema?.oneOf) ? schema.oneOf : [];
    const index = Number(field.dataset.unionVariantIndex || "0");
    const variant = variants[index];
    if (!variant) {
      throw new Error(`${label}: invalid union option`);
    }
    if (isNullSchemaVariant(variant)) {
      return null;
    }
    const nested = field.querySelector(":scope > .param-object-fields > .param-field");
    if (!nested) {
      throw new Error(`${label}: union value editor is missing`);
    }
    return readParamFieldValue(nested, variant, label);
  }

  const input = field.querySelector(":scope .param-input");
  if (!input) {
    throw new Error(`${label}: input is missing`);
  }
  const rawValue = String(input.value ?? "").trim();

  if (type === "bool") {
    return rawValue === "true";
  }
  if (type === "enum") {
    if (!rawValue) {
      throw new Error(`${label}: value is required`);
    }
    return rawValue;
  }
  if (type === "int") {
    if (!/^-?\d+$/.test(rawValue)) {
      throw new Error(`${label}: expected integer`);
    }
    const value = Number(rawValue);
    if (schema?.min !== undefined) {
      if (schema.exclusive_min ? value <= Number(schema.min) : value < Number(schema.min)) {
        throw new Error(`${label}: must be ${schema.exclusive_min ? ">" : ">="} ${schema.min}`);
      }
    }
    if (schema?.max !== undefined) {
      if (schema.exclusive_max ? value >= Number(schema.max) : value > Number(schema.max)) {
        throw new Error(`${label}: must be ${schema.exclusive_max ? "<" : "<="} ${schema.max}`);
      }
    }
    return value;
  }
  if (type === "float") {
    if (rawValue === "" || Number.isNaN(Number(rawValue))) {
      throw new Error(`${label}: expected number`);
    }
    const value = Number(rawValue);
    if (schema?.min !== undefined) {
      if (schema.exclusive_min ? value <= Number(schema.min) : value < Number(schema.min)) {
        throw new Error(`${label}: must be ${schema.exclusive_min ? ">" : ">="} ${schema.min}`);
      }
    }
    if (schema?.max !== undefined) {
      if (schema.exclusive_max ? value >= Number(schema.max) : value > Number(schema.max)) {
        throw new Error(`${label}: must be ${schema.exclusive_max ? "<" : "<="} ${schema.max}`);
      }
    }
    return value;
  }
  return rawValue;
}

export function readParamsFromHost(tool, form) {
  const schemaMap = tool?.params_schema && typeof tool.params_schema === "object" ? tool.params_schema : {};
  const params = {};
  for (const [key, schema] of Object.entries(schemaMap)) {
    const field = form.querySelector(`:scope > .param-field[data-param-key="${CSS.escape(key)}"]`);
    if (!field) {
      throw new Error(`${key}: field is missing`);
    }
    params[key] = readParamFieldValue(field, schema, key);
  }
  return params;
}

export function renderParamsHost(host, tool, initialParams = null, onChange = null) {
  host.innerHTML = "";
  const schemaMap = tool?.params_schema && typeof tool.params_schema === "object" ? tool.params_schema : {};
  const values = initialParams && typeof initialParams === "object" && !Array.isArray(initialParams)
    ? initialParams
    : resolvedDefaultParams(tool);

  for (const [key, schema] of Object.entries(schemaMap)) {
    const field = createParamFieldShell({ key, schema });
    renderParamField(field, schema, values[key] !== undefined ? values[key] : defaultForSchema(schema), onChange);
    host.appendChild(field);
  }

  bindInputListeners(host, onChange);
}

export function deepEqualJson(a, b) {
  if (a === b) {
    return true;
  }
  if (a === null || b === null) {
    return a === b;
  }
  if (typeof a !== typeof b) {
    return false;
  }
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) {
      return false;
    }
    for (let idx = 0; idx < a.length; idx += 1) {
      if (!deepEqualJson(a[idx], b[idx])) {
        return false;
      }
    }
    return true;
  }
  if (typeof a === "object") {
    const aKeys = Object.keys(a).sort();
    const bKeys = Object.keys(b).sort();
    if (aKeys.length !== bKeys.length) {
      return false;
    }
    for (let idx = 0; idx < aKeys.length; idx += 1) {
      if (aKeys[idx] !== bKeys[idx]) {
        return false;
      }
    }
    for (const key of aKeys) {
      if (!deepEqualJson(a[key], b[key])) {
        return false;
      }
    }
    return true;
  }
  return false;
}
