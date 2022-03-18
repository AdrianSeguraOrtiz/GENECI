ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 1) { 
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript PCIT.R input.csv \n") 
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

# Load CeTF
tryCatch(suppressMessages(library(CeTF)),
 error = function(e) BiocManager::install("CeTF"),
 finally = function(f) suppressMessages(library(CeTF)))

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
l.pcit_res <- PCIT(ex_matrix, tolType = "mean")

# Select only the significant correlation
prov_list <- l.pcit_res$tab[,-3]

# Return the absolute value because we are not interested in the sense of regulation
prov_list[,3] <- abs(prov_list[,3])

# Sort the list in descending order
conf_list <- prov_list[order(prov_list[,3], decreasing=T),]

# Rescale and remove rows with 0 confidence
conf_list <- ProcessList(conf_list)

# Save list
file_id <- tools::file_path_sans_ext(basename(in_file))
write.table(conf_list, paste0("./inferred_networks/", file_id, "/lists/GRN_PCIT.csv"), sep=",", col.names=F, row.names=F, quote=F)

