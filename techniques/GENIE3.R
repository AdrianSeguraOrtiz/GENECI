ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) { 
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as output identifier string \n")
    out_id <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript GENIE3.R input.csv out_id \n") 
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

# Install GENIE3
#BiocManager::install("GENIE3")

# Load GENIE3
suppressMessages(library(GENIE3))

# Load the expression matrix
ex_matrix <- as.matrix(read.table(in_file, sep=",", head=T, row.names=1))

# Infer gene regulatory network
## Random Forest regression (RF)
network_RF <- GENIE3(ex_matrix, treeMethod="RF")
conf_list_RF <- GetConfList(network_RF)

# Delete all rows with confidence 0
conf_list_RF <- conf_list_RF[conf_list_RF[,3] != 0, ]

# Save list
write.table(conf_list_RF, paste0(out_id, "_RF.csv"), sep=",", col.names=F, row.names=F, quote=F)

## ExtraTrees regression (ET)
network_ET <- GENIE3(ex_matrix, treeMethod="ET")
conf_list_ET <- GetConfList(network_ET)

# Delete all rows with confidence 0
conf_list_ET <- conf_list_ET[conf_list_ET[,3] != 0, ]

# Save list
write.table(conf_list_ET, paste0(out_id, "_ET.csv"), sep=",", col.names=F, row.names=F, quote=F)


