ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) == 1) { 
    if (ARGS[1] == "--help") {
        cat("Usage: \n")
        cat("Rscript BC3NET.R input.csv \n") 
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

# Install bc3net if not already installed
if(! "bc3net" %in% installed.packages()[,"Package"]) install.packages("bc3net")

# Load bc3net
library(bc3net)

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
network <- bc3net(ex_matrix, igraph=F)
conf_list <- GetConfList(network)

# Save list
write.csv(out_file, conf_list)