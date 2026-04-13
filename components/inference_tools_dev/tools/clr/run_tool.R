#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  suppressWarnings(library(jsonlite))
  suppressWarnings(library(minet))
})

`%||%` <- function(x, y) {
  if (is.null(x)) y else x
}

parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  out <- list()
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]
    if (!startsWith(key, "--")) {
      stop(sprintf("Unknown argument: %s", key), call. = FALSE)
    }
    if (i == length(args)) {
      stop(sprintf("Missing value for %s", key), call. = FALSE)
    }
    value <- args[[i + 1L]]
    if (startsWith(value, "--")) {
      stop(sprintf("Missing value for %s", key), call. = FALSE)
    }
    out[[substring(key, 3L)]] <- value
    i <- i + 2L
  }
  out
}

write_progress <- function(progress_path, status, percent, phase, message, error = NULL) {
  payload <- list(
    status = status,
    phase = phase,
    percent = max(0L, min(100L, as.integer(percent))),
    message = message,
    timestamp = as.numeric(Sys.time())
  )
  if (!is.null(error)) {
    payload$error <- as.character(error)
  }

  tmp_path <- paste0(progress_path, ".tmp")
  writeLines(toJSON(payload, auto_unbox = TRUE, null = "null"), tmp_path, useBytes = TRUE)
  if (!file.rename(tmp_path, progress_path)) {
    stop("Failed to write progress.json atomically.", call. = FALSE)
  }
}

is_scalar_number <- function(x) is.numeric(x) && length(x) == 1L && !is.na(x)
is_scalar_string <- function(x) is.character(x) && length(x) == 1L && !is.na(x)

load_params <- function(params_path) {
  params <- fromJSON(params_path, simplifyVector = TRUE)
  if (!is.list(params)) {
    stop("params.json must be a JSON object.", call. = FALSE)
  }
  params
}

resolve_params <- function(raw_params) {
  expected <- c("estimator", "disc", "nbins")
  missing <- setdiff(expected, names(raw_params))
  if (length(missing) > 0L) {
    stop(
      sprintf("Missing required params in params.json: %s", paste(missing, collapse = ", ")),
      call. = FALSE
    )
  }

  unknown <- setdiff(names(raw_params), expected)
  if (length(unknown) > 0L) {
    warning(sprintf("Unknown params ignored: %s", paste(sort(unknown), collapse = ", ")))
  }

  estimator <- raw_params$estimator
  disc <- raw_params$disc
  nbins <- raw_params$nbins

  estimator_values <- c(
    "mi.empirical", "mi.mm", "mi.shrink", "mi.sg",
    "pearson", "spearman", "kendall"
  )
  disc_values <- c("none", "equalfreq", "equalwidth", "globalequalwidth")

  if (!is_scalar_string(estimator) || !(estimator %in% estimator_values)) {
    stop(
      sprintf("estimator must be one of: %s", paste(estimator_values, collapse = ", ")),
      call. = FALSE
    )
  }
  if (!is_scalar_string(disc) || !(disc %in% disc_values)) {
    stop(
      sprintf("disc must be one of: %s", paste(disc_values, collapse = ", ")),
      call. = FALSE
    )
  }

  if (!is.null(nbins)) {
    if (!is_scalar_number(nbins) || abs(nbins - round(nbins)) > 1e-9) {
      stop("nbins must be null or an integer >= 1.", call. = FALSE)
    }
    nbins <- as.integer(round(nbins))
    if (nbins < 1L) {
      stop("nbins must be >= 1 when provided.", call. = FALSE)
    }
  }

  list(
    estimator = estimator,
    disc = disc,
    nbins = nbins
  )
}

read_expression_tsv <- function(expr_path) {
  df <- read.delim(
    expr_path,
    sep = "\t",
    header = TRUE,
    check.names = FALSE,
    stringsAsFactors = FALSE
  )
  if (ncol(df) < 2L) {
    stop("expression.tsv must have at least 2 columns: gene + >=1 observation.", call. = FALSE)
  }

  gene_col <- names(df)[1L]
  df <- df[!duplicated(df[[gene_col]]), , drop = FALSE]

  genes <- as.character(df[[gene_col]])
  observations <- names(df)[-1L]

  num_df <- data.frame(
    lapply(df[, -1L, drop = FALSE], function(x) as.numeric(x)),
    check.names = FALSE
  )
  if (anyNA(as.matrix(num_df))) {
    stop("expression.tsv contains non-numeric values in observation columns.", call. = FALSE)
  }

  mat <- as.matrix(num_df)
  rownames(mat) <- genes
  obs_x_genes <- t(mat)
  rownames(obs_x_genes) <- observations
  colnames(obs_x_genes) <- genes
  obs_x_genes
}

infer_clr <- function(expression_data, params) {
  mim_args <- list(
    dataset = expression_data,
    estimator = params$estimator,
    disc = params$disc
  )
  if (!is.null(params$nbins)) {
    mim_args$nbins <- params$nbins
  }

  mim <- do.call(minet::build.mim, mim_args)
  if (!is.matrix(mim)) {
    stop("minet::build.mim did not return a matrix.", call. = FALSE)
  }

  score_matrix <- minet::clr(mim)
  if (!is.matrix(score_matrix)) {
    stop("minet::clr did not return a matrix.", call. = FALSE)
  }
  if (nrow(score_matrix) != ncol(score_matrix)) {
    stop("CLR score matrix must be square.", call. = FALSE)
  }
  if (is.null(rownames(score_matrix)) || is.null(colnames(score_matrix))) {
    stop("CLR score matrix is missing row/column names.", call. = FALSE)
  }
  score_matrix
}

build_network <- function(score_matrix) {
  genes <- rownames(score_matrix)
  n_genes <- length(genes)
  if (n_genes < 2L) {
    stop("CLR requires at least 2 genes to build a non-empty network.", call. = FALSE)
  }

  rows <- list()
  for (i in seq_len(n_genes - 1L)) {
    for (j in seq.int(i + 1L, n_genes)) {
      score <- as.numeric(score_matrix[j, i])
      if (!is.finite(score)) {
        stop(
          sprintf(
            "Non-finite CLR score for gene pair (%s, %s).",
            genes[[i]],
            genes[[j]]
          ),
          call. = FALSE
        )
      }
      if (score == 0) {
        next
      }
      rows[[length(rows) + 1L]] <- data.frame(
        source = genes[[i]],
        target = genes[[j]],
        score = score,
        sign = "?",
        evidence = "association",
        context = "global",
        stringsAsFactors = FALSE
      )
    }
  }

  if (!length(rows)) {
    stop("CLR produced no non-zero interactions for this dataset.", call. = FALSE)
  }
  out <- do.call(rbind, rows)
  out[order(out$score, decreasing = TRUE), , drop = FALSE]
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

  write_progress(progress_path, "running", 0L, "init", "Initializing CLR wrapper")

  tryCatch({
    raw_params <- load_params(params_path)
    params <- resolve_params(raw_params)

    write_progress(progress_path, "running", 10L, "load_input", "Loading expression matrix")
    expression_data <- read_expression_tsv(input_path)

    write_progress(
      progress_path,
      "running",
      30L,
      "inference",
      "Running minet::build.mim + minet::clr"
    )
    score_matrix <- infer_clr(expression_data, params)

    write_progress(progress_path, "running", 90L, "write_output", "Writing network.csv")
    network_df <- build_network(score_matrix)
    write.csv(
      network_df,
      file.path(output_dir, "network.csv"),
      row.names = FALSE
    )

    write_progress(progress_path, "completed", 100L, "done", "CLR completed successfully")
  }, error = function(exc) {
    write_progress(
      progress_path,
      "failed",
      100L,
      "error",
      "CLR failed",
      error = conditionMessage(exc)
    )
    stop(exc)
  })
}

main()
