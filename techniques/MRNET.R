ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) { 
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as output identifier string \n")
    out_id <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript MRNET.R input.csv out_id \n") 
    cat("Arguments required: \n")
    cat("\t 1) CSV input file \n")
    cat("\t 2) Output identifier string \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 2) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Load functions
source("./functions/functions.R")

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install minet
#BiocManager::install("minet")

# Load minet
suppressMessages(library(minet))

# Load the expression matrix
ex_matrix <- t(read.table(in_file, sep=",", head=T, row.names=1))

# Infer gene regulatory network
network <- minet(ex_matrix, method="mrnet")
conf_list <- GetConfList(network)

# Rescale and remove rows with 0 confidence
conf_list <- ProcessList(conf_list)

# Save list
write.table(conf_list, paste0(out_id, ".csv"), sep=",", col.names=F, row.names=F, quote=F)
