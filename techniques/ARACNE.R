# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install minet and GENIE3
#BiocManager::install("minet")
#BiocManager::install("GENIE3")

# Load minet and GENIE3
library(minet)
library(GENIE3)

in_file <- '../data/DREAM4/EXP/dream4_010_01_exp.csv'

# Load the expression matrix
ex_matrix <- t(read.table(in_file, sep=",", head=T, row.names=1))

# Infer gene regulatory network
network <- minet(ex_matrix, method="aracne")
conf_list <- getLinkList(network)
head(conf_list)
