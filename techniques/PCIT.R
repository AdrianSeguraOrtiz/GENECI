# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install CeTF
#BiocManager::install("CeTF")

# Load CeTF
library(CeTF)

in_file <- '../data/DREAM4/EXP/dream4_010_01_exp.csv'

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

head(conf_list)

