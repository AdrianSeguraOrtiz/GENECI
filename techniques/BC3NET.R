# Load functions
source("./functions/functions.R")

# Install bc3net if not already installed
if(! "bc3net" %in% installed.packages()[,"Package"]) install.packages("bc3net")

# Load bc3net
library(bc3net)

in_file <- '../data/DREAM4/EXP/dream4_010_01_exp.csv'

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
network <- bc3net(ex_matrix, igraph=F)
conf_list <- GetConfList(network)
head(conf_list)