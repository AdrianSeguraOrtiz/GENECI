#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  suppressWarnings(library(jsonlite))
  suppressWarnings(library(tigress))
})

`%||%` <- function(x, y) {
  if (is.null(x)) y else x
}

parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  out <- list()
  i <- 1
  while (i <= length(args)) {
    key <- args[[i]]
    if (!startsWith(key, "--")) {
      stop(sprintf("Unknown argument: %s", key), call. = FALSE)
    }
    if (i == length(args)) {
      stop(sprintf("Missing value for %s", key), call. = FALSE)
    }
    value <- args[[i + 1]]
    if (startsWith(value, "--")) {
      stop(sprintf("Missing value for %s", key), call. = FALSE)
    }
    out[[substring(key, 3)]] <- value
    i <- i + 2
  }
  out
}

write_progress <- function(progress_path, status, percent, phase, message,
                           completed = NULL, total = NULL, error = NULL) {
  payload <- list(
    status = status,
    phase = phase,
    percent = max(0L, min(100L, as.integer(percent))),
    message = message,
    timestamp = as.numeric(Sys.time())
  )
  if (!is.null(completed)) payload$completed <- as.integer(completed)
  if (!is.null(total)) payload$total <- as.integer(total)
  if (!is.null(error)) payload$error <- as.character(error)

  tmp_path <- paste0(progress_path, ".tmp")
  writeLines(toJSON(payload, auto_unbox = TRUE, null = "null"), tmp_path, useBytes = TRUE)
  if (!file.rename(tmp_path, progress_path)) {
    stop("Failed to write progress.json atomically.", call. = FALSE)
  }
}

is_scalar_logical <- function(x) is.logical(x) && length(x) == 1L && !is.na(x)
is_scalar_number <- function(x) is.numeric(x) && length(x) == 1L && !is.na(x)
is_scalar_string <- function(x) is.character(x) && length(x) == 1L && !is.na(x)

as_int_checked <- function(name, x, min_value = NULL) {
  if (!is_scalar_number(x) || abs(x - round(x)) > 1e-9) {
    stop(sprintf("%s must be an integer.", name), call. = FALSE)
  }
  xi <- as.integer(round(x))
  if (!is.null(min_value) && xi < min_value) {
    stop(sprintf("%s must be >= %d.", name, as.integer(min_value)), call. = FALSE)
  }
  xi
}

load_params <- function(params_path) {
  params <- fromJSON(params_path, simplifyVector = TRUE)
  if (!is.list(params)) {
    stop("params.json must be a JSON object.", call. = FALSE)
  }
  params
}

resolve_params <- function(raw_params) {
  required <- c(
    "alpha", "nstepsLARS", "nsplit", "normalizeexp", "scoring",
    "allsteps", "usemulticore", "limit", "seed"
  )
  missing <- setdiff(required, names(raw_params))
  if (length(missing) > 0L) {
    stop(sprintf("Missing required params in params.json: %s", paste(missing, collapse = ", ")), call. = FALSE)
  }

  alpha <- raw_params$alpha
  nstepsLARS <- raw_params$nstepsLARS
  nsplit <- raw_params$nsplit
  normalizeexp <- raw_params$normalizeexp
  scoring <- raw_params$scoring
  allsteps <- raw_params$allsteps
  usemulticore <- raw_params$usemulticore
  limit <- raw_params$limit
  seed <- raw_params$seed

  if (!is_scalar_number(alpha) || alpha < 0 || alpha > 1) {
    stop("alpha must be a number in [0, 1].", call. = FALSE)
  }
  nstepsLARS <- as_int_checked("nstepsLARS", nstepsLARS, min_value = 1)
  nsplit <- as_int_checked("nsplit", nsplit, min_value = 1)

  if (!is_scalar_logical(normalizeexp)) stop("normalizeexp must be a boolean.", call. = FALSE)
  if (!is_scalar_string(scoring) || !(scoring %in% c("area", "max"))) {
    stop("scoring must be one of: area, max.", call. = FALSE)
  }
  if (!is_scalar_logical(allsteps)) stop("allsteps must be a boolean.", call. = FALSE)
  if (!is_scalar_logical(usemulticore)) stop("usemulticore must be a boolean.", call. = FALSE)

  if (!is.null(limit)) {
    limit <- as_int_checked("limit", limit, min_value = 1)
  }
  if (!is.null(seed)) {
    seed <- as_int_checked("seed", seed, min_value = 0)
  }

  list(
    alpha = as.numeric(alpha),
    nstepsLARS = nstepsLARS,
    nsplit = nsplit,
    normalizeexp = normalizeexp,
    scoring = scoring,
    allsteps = allsteps,
    usemulticore = usemulticore,
    limit = limit,
    seed = seed
  )
}

load_tf_list <- function(extra_dir) {
  tf_path <- file.path(extra_dir, "tf_list.txt")
  if (!file.exists(tf_path)) {
    return(NULL)
  }
  raw <- readLines(tf_path, warn = FALSE)
  raw <- trimws(raw)
  tfs <- raw[nzchar(raw) & !startsWith(raw, "#")]
  if (length(tfs) == 0L) NULL else tfs
}

read_expression_tsv <- function(expr_path) {
  df <- read.delim(expr_path, sep = "\t", header = TRUE, check.names = FALSE, stringsAsFactors = FALSE)
  if (ncol(df) < 2L) {
    stop("expression.tsv must have at least 2 columns: gene + >=1 observation.", call. = FALSE)
  }

  gene_col <- names(df)[1]
  df <- df[!duplicated(df[[gene_col]]), , drop = FALSE]

  genes <- as.character(df[[gene_col]])
  num_df <- data.frame(lapply(df[, -1, drop = FALSE], function(x) as.numeric(x)), check.names = FALSE)
  if (anyNA(as.matrix(num_df))) {
    stop("expression.tsv contains non-numeric values in observation columns.", call. = FALSE)
  }

  mat <- as.matrix(num_df)
  rownames(mat) <- genes
  obs_x_genes <- t(mat)
  colnames(obs_x_genes) <- genes
  obs_x_genes
}

# Upstream TIGRESS can index past the available LARS steps on small/collinear datasets.
# Retry with fewer steps so the wrapper remains usable instead of failing outright.
run_tigress_with_fallback <- function(expression_data, tf_names, params) {
  requested_steps <- params$nstepsLARS
  last_error <- NULL

  for (steps in seq.int(requested_steps, 1L, by = -1L)) {
    result <- tryCatch(
      tigress::tigress(
        expdata = expression_data,
        tflist = tf_names,
        targetlist = colnames(expression_data),
        alpha = params$alpha,
        nstepsLARS = steps,
        nsplit = params$nsplit,
        normalizeexp = params$normalizeexp,
        scoring = params$scoring,
        allsteps = params$allsteps,
        verb = FALSE,
        usemulticore = params$usemulticore
      ),
      error = function(e) e
    )

    if (!inherits(result, "error")) {
      if (steps != requested_steps) {
        message(
          sprintf(
            "Adjusted nstepsLARS from %d to %d because TIGRESS/lars could not realize the requested step count on this dataset.",
            requested_steps,
            steps
          )
        )
      }
      return(list(result = result, effective_nstepsLARS = steps))
    }

    last_error <- result
    if (!grepl("subscript out of bounds", conditionMessage(result), fixed = TRUE) || steps == 1L) {
      stop(result)
    }
  }

  stop(last_error)
}

build_network <- function(score_matrix, limit) {
  edge_df <- as.data.frame(as.table(score_matrix), stringsAsFactors = FALSE)
  names(edge_df) <- c("source", "target", "score")
  edge_df$score <- as.numeric(edge_df$score)
  edge_df <- edge_df[is.finite(edge_df$score) & edge_df$score != 0, , drop = FALSE]
  if (!nrow(edge_df)) {
    stop("TIGRESS produced no non-zero interactions for this dataset.", call. = FALSE)
  }
  edge_df <- edge_df[order(edge_df$score, decreasing = TRUE), , drop = FALSE]

  if (!is.null(limit) && nrow(edge_df) > limit) {
    edge_df <- edge_df[seq_len(limit), , drop = FALSE]
  }

  edge_df$sign <- "?"
  edge_df$evidence <- "association"
  edge_df$context <- "global"
  edge_df[, c("source", "target", "score", "sign", "evidence", "context"), drop = FALSE]
}

main <- function() {
  args <- parse_args()
  input_path <- args$input %||% stop("Missing required argument: --input", call. = FALSE)
  params_path <- args$params %||% stop("Missing required argument: --params", call. = FALSE)
  extra_dir <- args$extra %||% stop("Missing required argument: --extra", call. = FALSE)
  output_dir <- args$`output-dir` %||% stop("Missing required argument: --output-dir", call. = FALSE)
  threads_raw <- args$threads %||% stop("Missing required argument: --threads", call. = FALSE)

  threads <- suppressWarnings(as.integer(threads_raw))
  if (is.na(threads) || threads <= 0L) {
    stop("--threads must be a positive integer.", call. = FALSE)
  }

  if (!file.exists(input_path)) stop(sprintf("Input file not found: %s", input_path), call. = FALSE)
  if (!file.exists(params_path)) stop(sprintf("Params file not found: %s", params_path), call. = FALSE)
  if (!dir.exists(extra_dir)) stop(sprintf("Extra directory not found: %s", extra_dir), call. = FALSE)

  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  progress_path <- file.path(output_dir, "progress.json")

  write_progress(progress_path, "running", 0L, "init", "Initializing")

  tryCatch({
    raw_params <- load_params(params_path)
    params <- resolve_params(raw_params)

    if (isTRUE(params$usemulticore) && threads <= 1L) {
      warning("usemulticore=TRUE but --threads<=1; running effectively single-core.")
    }

    if (!is.null(params$seed)) {
      set.seed(params$seed)
    }

    write_progress(progress_path, "running", 5L, "load_input", "Loading expression and extra inputs")
    expression_data <- read_expression_tsv(input_path)
    tf_names <- load_tf_list(extra_dir)
    if (is.null(tf_names)) {
      tf_names <- colnames(expression_data)
    }

    write_progress(
      progress_path,
      "running",
      10L,
      "inference",
      "Running TIGRESS (no fine-grained internal progress available)"
    )

    tigress_run <- run_tigress_with_fallback(expression_data, tf_names, params)
    tigress_result <- tigress_run$result

    score_matrix <- if (is.list(tigress_result)) {
      tigress_result[[length(tigress_result)]]
    } else {
      tigress_result
    }

    if (!is.matrix(score_matrix)) {
      stop("Unexpected TIGRESS output: expected matrix or list of matrices.", call. = FALSE)
    }

    write_progress(progress_path, "running", 96L, "write_output", "Writing network.csv")
    out_df <- build_network(score_matrix, params$limit)
    write.csv(out_df, file.path(output_dir, "network.csv"), row.names = FALSE)

    write_progress(
      progress_path,
      "completed",
      100L,
      "done",
      "Inference finished",
      completed = nrow(out_df),
      total = nrow(out_df)
    )
  }, error = function(e) {
    write_progress(
      progress_path,
      "failed",
      100L,
      "failed",
      "Inference failed",
      error = conditionMessage(e)
    )
    stop(e)
  })
}

main()
