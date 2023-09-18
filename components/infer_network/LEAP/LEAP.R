ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) { 
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as output folder \n")
    output_folder <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript LEAP.R input.csv path/to/output_folder \n") 
    cat("Arguments required: \n")
    cat("\t 1) CSV input file \n")
    cat("\t 2) Path to output folder \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 2) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Load functions
source("components/infer_network/functions.R")

# Install leap if not already installed
if(! "LEAP" %in% installed.packages()[,"Package"]) install.packages("LEAP")

# Load LEAP
suppressMessages(library(LEAP))

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)
genes <- rownames(ex_matrix)

# Infer gene regulatory network
rownames(ex_matrix) <- NULL
leap_table <- MAC_counter(data = ex_matrix)
source <- genes[leap_table[, 3]]
tarjet <- genes[leap_table[, 4]]
conf <- abs(leap_table[, 1])
conf_list <- data.frame(source, tarjet, conf)

# Rescale and remove rows with 0 confidence
conf_list <- ProcessList(conf_list)

# Save list
file_id <- tools::file_path_sans_ext(basename(in_file))
write.table(conf_list, paste0("./", output_folder, "/GRN_LEAP.csv"), sep=",", col.names=F, row.names=F, quote=F)
