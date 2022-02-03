ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) == 1) { 
    if (ARGS[1] == "--help") {
        cat("Usage: \n")
        cat("Rscript C3NET.R input.csv \n") 
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

# Install c3net if not already installed
if(! "c3net" %in% installed.packages()[,"Package"]) install.packages("c3net")

# Load c3net
library(c3net)

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
network <- c3net(ex_matrix)
conf_list <- GetConfList(network)

# Save list
write.csv(out_file, conf_list)