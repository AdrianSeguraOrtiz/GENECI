# Install bc3net if not already installed
if(! "bc3net" %in% installed.packages()[,"Package"]) install.packages("bc3net")

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install GENIE3
#BiocManager::install("GENIE3")

# Load bc3net and GENIE3
library(bc3net)
library(GENIE3)

in_file <- '../data/DREAM4/EXP/dream4_010_01_exp.csv'

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
network <- bc3net(ex_matrix, igraph=F)
conf_list <- getLinkList(network)
head(conf_list)