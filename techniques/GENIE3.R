# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install GENIE3
#BiocManager::install("GENIE3")

# Load GENIE3
library(GENIE3)

in_file <- '../data/DREAM4/EXP/dream4_010_01_exp.csv'

# Load the expression matrix
ex_matrix <- as.matrix(read.table(in_file, sep=",", head=T, row.names=1))

# Infer gene regulatory network
## Random Forest regression (RF)
network_RF <- GENIE3(ex_matrix, treeMethod="RF")
conf_list_RF <- getLinkList(network_RF)
head(conf_list_RF)

## ExtraTrees regression (ET)
network_ET <- GENIE3(ex_matrix, treeMethod="ET")
conf_list_ET <- getLinkList(network_ET)
head(conf_list_ET)


