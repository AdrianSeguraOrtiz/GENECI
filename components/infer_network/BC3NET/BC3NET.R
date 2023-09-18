ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) { 
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as output folder \n")
    output_folder <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript BC3NET.R input.csv path/to/output_folder \n") 
    cat("Arguments required: \n")
    cat("\t 1) CSV input file \n")
    cat("\t 2) Path to output folder \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 2) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Load functions
source("components/infer_network/functions.R")

# Install bc3net if not already installed
if(! "bc3net" %in% installed.packages()[,"Package"]) install.packages("bc3net")

# Load bc3net
suppressMessages(library(bc3net))

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
network <- bc3net(ex_matrix, igraph=F)
dt.cl <- GetConfList(network)
colnames(dt.cl)[3] <- paste0(colnames(dt.cl)[3], "_1")

for (i in 2:11) {
    network <- bc3net(ex_matrix, igraph=F)
    conf_list_i <- GetConfList(network)
    dt.cl <- merge(dt.cl, conf_list_i, by=c(1,2), all.x=TRUE, all.y=TRUE, suffixes = c("", paste0("_", i)))
}

dt.cl$Conf <- apply(dt.cl[,-c(1,2)], 1, median)
conf_list <- dt.cl[, c(1,2,ncol(dt.cl))]

# Rescale and remove rows with 0 confidence
conf_list <- ProcessList(conf_list)

# Save list
file_id <- tools::file_path_sans_ext(basename(in_file))
write.table(conf_list, paste0("./", output_folder, "/GRN_BC3NET.csv"), sep=",", col.names=F, row.names=F, quote=F)