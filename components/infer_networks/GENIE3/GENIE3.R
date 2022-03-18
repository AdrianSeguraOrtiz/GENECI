ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 1) { 
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript GENIE3.R input.csv \n") 
    cat("Arguments required: \n")
    cat("\t 1) CSV input file \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 1) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Load functions
source("components/infer_networks/functions.R")

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Load GENIE3
tryCatch(suppressMessages(library(GENIE3)),
 error = function(e) BiocManager::install("GENIE3"),
 finally = function(f) suppressMessages(library(GENIE3)))

# Load the expression matrix
ex_matrix <- as.matrix(read.table(in_file, sep=",", head=T, row.names=1))

# Infer gene regulatory network
## Random Forest regression (RF)
network_RF <- GENIE3(ex_matrix, treeMethod="RF")
conf_list_RF <- GetConfList(network_RF)

## ExtraTrees regression (ET)
network_ET <- GENIE3(ex_matrix, treeMethod="ET")
conf_list_ET <- GetConfList(network_ET)

# Rescale and remove rows with 0 confidence
conf_list_RF <- ProcessList(conf_list_RF)
conf_list_ET <- ProcessList(conf_list_ET)

# Save lists
file_id <- tools::file_path_sans_ext(basename(in_file))
write.table(conf_list_RF, paste0("./inferred_networks/", file_id, "/lists/GRN_GENIE3_RF.csv"), sep=",", col.names=F, row.names=F, quote=F)
write.table(conf_list_ET, paste0("./inferred_networks/", file_id, "/lists/GRN_GENIE3_ET.csv"), sep=",", col.names=F, row.names=F, quote=F)
