# Install c3net if not already installed
if(! "c3net" %in% installed.packages()[,"Package"]) install.packages("c3net")

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install GENIE3
#BiocManager::install("GENIE3")

# Load c3net and GENIE3
library(c3net)
library(GENIE3)

in_file <- '../data/DREAM4/EXP/dream4_010_01_exp.csv'

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
network <- c3net(ex_matrix)
conf_list <- getLinkList(network)
head(conf_list)