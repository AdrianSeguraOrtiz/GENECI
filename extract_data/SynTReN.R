# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Load grndata
tryCatch(suppressMessages(library(grndata)),
 error = function(e) BiocManager::install("grndata"),
 finally = function(f) suppressMessages(library(grndata)))

# Select the data to be downloaded
v.str_networks <- c("syntren300", "syntren1000")

# Saving data in CSV files
for (str_n in v.str_networks) {

    # Get data
    l.data <- getData(datasource.name=str_n)

    # Extract expression data
    mtx.exp <- t(l.data[[1]])

    # Save expression data
    write.table(mtx.exp, paste0("../expression_data/SynTReN/EXP/", str_n, "_exp.csv"), sep=",", col.names = NA)

    # Extract gold standard adjacency matrix
    mtx.gs <- l.data[[2]]

    # Save gold standard
    write.table(mtx.gs, paste0("../expression_data/SynTReN/GS/", str_n, "_gs.csv"), sep=",", col.names = NA)
}