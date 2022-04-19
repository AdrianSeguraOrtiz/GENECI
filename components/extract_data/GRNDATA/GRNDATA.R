ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) { 
    cat("ARGS == 1: the argument will be treated as database name \n")
    database <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as output folder \n")
    output_folder <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript GRNDATA.R database_name path/to/output_folder \n") 
    cat("Arguments required: \n")
    cat("\t 1) Database name: SynTReN|Rogers|GeneNetWeaver \n")
    cat("\t 2) Path to output folder \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 2) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Load grndata
tryCatch(suppressMessages(library(grndata)),
error = function(e) BiocManager::install("grndata"),
finally = function(f) suppressMessages(library(grndata)))

# Select the data to be downloaded
v.str_networks <- NULL
if (database == "GeneNetWeaver") {
    v.str_networks <- c("gnw1565", "gnw2000")
} else if (database == "Rogers") {
    v.str_networks <- c("rogers1000")
} else if (database == "SynTReN") {
    v.str_networks <- c("syntren300", "syntren1000")
}

# Saving data in CSV files
for (str_n in v.str_networks) {

    # Get data
    l.data <- getData(datasource.name=str_n)

    # Extract expression data
    mtx.exp <- t(l.data[[1]])

    # Save expression data
    write.table(mtx.exp, paste0("./", output_folder, "/", database, "/EXP/", str_n, "_exp.csv"), sep=",", col.names = NA)

    # Extract gold standard adjacency matrix
    mtx.gs <- l.data[[2]]

    # Save gold standard
    write.table(mtx.gs, paste0("./", output_folder, "/", database, "/GS/", str_n, "_gs.csv"), sep=",", col.names = NA)
}
