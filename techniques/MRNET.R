ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) == 1) { 
    if (ARGS[1] == "--help") {
        cat("Usage: \n")
        cat("Rscript MRNET.R input.csv \n") 
        cat("Arguments required: \n")
        cat("\t 1) CSV input file \n")
        stop("", call. = FALSE)
    } else {
        cat("ARGS == 1: the argument will be treated as input csv file \n")
        in_file <- ARGS[1]
    }
} else if (length(ARGS) != 1) {
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
library(minet)

# Load the expression matrix
ex_matrix <- t(read.table(in_file, sep=",", head=T, row.names=1))

# Infer gene regulatory network
network <- minet(ex_matrix, method="mrnet")
conf_list <- GetConfList(network)

# Save list
write.csv(out_file, conf_list)
