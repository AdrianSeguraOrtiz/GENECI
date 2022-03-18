ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 1) { 
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript BC3NET.R input.csv \n") 
    cat("Arguments required: \n")
    cat("\t 1) CSV input file \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 1) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Load functions
source("components/infer_networks/functions.R")

# Install bc3net if not already installed
if(! "bc3net" %in% installed.packages()[,"Package"]) install.packages("bc3net")

# Load bc3net
suppressMessages(library(bc3net))

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
network <- bc3net(ex_matrix, igraph=F)
conf_list <- GetConfList(network)

# Rescale and remove rows with 0 confidence
conf_list <- ProcessList(conf_list)

# Save list
file_id <- tools::file_path_sans_ext(basename(in_file))
write.table(conf_list, paste0("./inferred_networks/", file_id, "/lists/GRN_BC3NET.csv"), sep=",", col.names=F, row.names=F, quote=F)