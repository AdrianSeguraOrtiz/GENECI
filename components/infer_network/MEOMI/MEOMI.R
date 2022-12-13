ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) {
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as output folder \n")
    output_folder <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript MEOMI.R input.csv path/to/output_folder \n")
    cat("Arguments required: \n")
    cat("\t 1) CSV input file \n")
    cat("\t 2) Path to output folder \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 2) {
    stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Load functions
source("components/infer_network/functions.R")
source("components/infer_network/MEOMI/src/manipulation_function.R")
source("components/infer_network/MEOMI/src/conditional_interaction_information_calculation.R")
source("components/infer_network/MEOMI/src/MEOMI.R")

# Install CRAN packages
lbs <- c("sqldf", "pROC", "parallel", "dplyr", "igraph", "rlang", "entropy", "modEvA", "reshape", "ROCR", "readr", "tidyr")
not_installed <- lbs[!(lbs %in% installed.packages()[, "Package"])]
if (length(not_installed)) install.packages(not_installed, repos = "http://cran.us.r-project.org")

# Load CRAN packages
suppressMessages(library(sqldf))
suppressMessages(library(igraph))
suppressMessages(library(rlang))
suppressMessages(library(dplyr))
suppressMessages(library(pROC))
suppressMessages(library(entropy))
suppressMessages(library(modEvA))
suppressMessages(library(parallel))
suppressMessages(library(reshape))
suppressMessages(library(ROCR))
suppressMessages(library(readr))
suppressMessages(library(tidyr))

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE)) {
    install.packages("BiocManager")
}

# Install and load BiocManager packages
tryCatch(suppressMessages(library(minet)),
    error = function(e) BiocManager::install("minet"),
    finally = function(f) suppressMessages(library(minet))
)

tryCatch(suppressMessages(library(Rgraphviz)),
    error = function(e) BiocManager::install("Rgraphviz"),
    finally = function(f) suppressMessages(library(Rgraphviz))
)

# Load the expression matrix
ex_matrix <- t(read.table(in_file, sep = ",", head = TRUE, row.names = 1))

# Infer gene regulatory network
conf_list <- MEOMI(mydata = ex_matrix, bins = 5, lamda = 0.1, order = 4)

# Rescale and remove rows with 0 confidence
conf_list <- ProcessList(conf_list)

# Save list
file_id <- tools::file_path_sans_ext(basename(in_file))
write.table(conf_list, paste0("./", output_folder, "/GRN_MEOMI.csv"), sep = ",", col.names = FALSE, row.names = FALSE, quote = FALSE)
