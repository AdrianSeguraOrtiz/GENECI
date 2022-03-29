ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) { 
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as output folder \n")
    output_folder <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript C3NET.R input.csv path/to/output_folder \n") 
    cat("Arguments required: \n")
    cat("\t 1) CSV input file \n")
    cat("\t 2) Path to output folder \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 2) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Load functions
source("components/infer_network/functions.R")

# Install c3net if not already installed
if(! "c3net" %in% installed.packages()[,"Package"]) install.packages("c3net")

# Load c3net
suppressMessages(library(c3net))

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
network <- c3net(ex_matrix)
conf_list <- GetConfList(network)

# Rescale and remove rows with 0 confidence
conf_list <- ProcessList(conf_list)

# Save list
file_id <- tools::file_path_sans_ext(basename(in_file))
write.table(conf_list, paste0("./", output_folder, "/", file_id, "/lists/GRN_C3NET.csv"), sep=",", col.names=F, row.names=F, quote=F)