ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) { 
    cat("ARGS == 1: the argument will be treated as category \n")
    category <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as output folder \n")
    output_folder <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript IRMA.R category path/to/output_folder \n") 
    cat("Arguments required: \n")
    cat("\t 1) Category: ExpressionData|GoldStandard \n")
    cat("\t 2) Path to output folder \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 2) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Load KBoost
tryCatch(suppressMessages(library(KBoost)),
error = function(e) BiocManager::install("KBoost"),
finally = function(f) suppressMessages(library(KBoost)))


if (category == "ExpressionData") {
    # Extract expression data
    data(irma_on)
    mtx.exp_on <- t(irma_on)
    data(irma_off)
    mtx.exp_off <- t(irma_off)

    # Save expression data
    write.table(mtx.exp_on, paste0("./", output_folder, "/IRMA/EXP/switch-on_exp.csv"), sep=",", col.names = NA)
    write.table(mtx.exp_off, paste0("./", output_folder, "/IRMA/EXP/switch-off_exp.csv"), sep=",", col.names = NA)

} else if (category == "GoldStandard") {
    # Extract gold standard adjacency matrix
    data(IRMA_Gold)

    # Save gold standard
    write.table(IRMA_Gold, paste0("./", output_folder, "/IRMA/GS/irma_gs.csv"), sep=",", col.names = NA)
}
