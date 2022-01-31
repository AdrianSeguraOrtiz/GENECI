# Load functions
source("./functions/functions.R")

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install minet
#BiocManager::install("minet")

# Load minet
library(minet)

in_file <- '../data/DREAM4/EXP/dream4_010_01_exp.csv'

# Load the expression matrix
ex_matrix <- t(read.table(in_file, sep=",", head=T, row.names=1))

# Infer gene regulatory network
network <- minet(ex_matrix, method="aracne")
conf_list <- GetConfList(network)


head(conf_list)
