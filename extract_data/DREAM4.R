# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install DREAM4
#BiocManager::install("DREAM4")

# Load DREAM4
library(DREAM4)

# Networks of 10 nodes
v.str_networks_10 <- c("dream4_010_01", "dream4_010_02", "dream4_010_03", "dream4_010_04", "dream4_010_05")
data(list = v.str_networks_10)

# Networks of 100 nodes
v.str_networks_100 <- c("dream4_100_01", "dream4_100_02", "dream4_100_03", "dream4_100_04", "dream4_100_05")
data(list = v.str_networks_100)

# List of all networks
v.str_networks <- c(v.str_networks_10, v.str_networks_100)
l.networks <- mget(v.str_networks)
names(l.networks) <- v.str_networks

# Saving data in CSV files
for (str_n in v.str_networks) {

    # Get data
    n <- l.networks[[str_n]]

    # Extract expression data
    mtx.exp <- assays(n)[[1]]

    # Remove the columns with time series data
    good_cols <- grep("\\.t", colnames(mtx.exp), invert=T)
    mtx.exp <- mtx.exp[, good_cols]

    # Save expression data
    write.table(mtx.exp, paste0("../data/DREAM4/EXP/", str_n, "_exp.csv"), sep=",", col.names = NA)

    # Extract gold standard adjacency matrix
    mtx.gs <- metadata(n)[[1]]

    # Save gold standard
    write.table(mtx.gs, paste0("../data/DREAM4/GS/", str_n, "_gs.csv"), sep=",", col.names = NA)
}

