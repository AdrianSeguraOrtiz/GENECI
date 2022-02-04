# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install grndata
#BiocManager::install("grndata")

# Load grndata
suppressMessages(library(grndata))

# Select the data to be downloaded
v.str_networks <- c("rogers1000")

# Saving data in CSV files
for (str_n in v.str_networks) {

    # Get data
    l.data <- getData(datasource.name=str_n)

    # Extract expression data
    mtx.exp <- t(l.data[[1]])

    # Save expression data
    write.table(mtx.exp, paste0("../data/Rogers/EXP/", str_n, "_exp.csv"), sep=",", col.names = NA)

    # Extract gold standard adjacency matrix
    mtx.gs <- l.data[[2]]

    # Save gold standard
    write.table(mtx.gs, paste0("../data/Rogers/GS/", str_n, "_gs.csv"), sep=",", col.names = NA)
}