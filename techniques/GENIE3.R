ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) == 1) { 
    if (ARGS[1] == "--help") {
        cat("Usage: \n")
        cat("Rscript GENIE3.R input.csv \n") 
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

# Install GENIE3
#BiocManager::install("GENIE3")

# Load GENIE3
library(GENIE3)

# Load the expression matrix
ex_matrix <- as.matrix(read.table(in_file, sep=",", head=T, row.names=1))

# Infer gene regulatory network
## Random Forest regression (RF)
network_RF <- GENIE3(ex_matrix, treeMethod="RF")
conf_list_RF <- GetConfList(network_RF)
head(conf_list_RF)

## ExtraTrees regression (ET)
network_ET <- GENIE3(ex_matrix, treeMethod="ET")
conf_list_ET <- GetConfList(network_ET)
head(conf_list_ET)


