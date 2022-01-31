# Load functions
source("./functions/functions.R")

# Install c3net if not already installed
if(! "c3net" %in% installed.packages()[,"Package"]) install.packages("c3net")

# Load c3net
library(c3net)

in_file <- '../data/DREAM4/EXP/dream4_010_01_exp.csv'

# Load the expression matrix
ex_matrix <- read.table(in_file, sep=",", head=T, row.names=1)

# Infer gene regulatory network
network <- c3net(ex_matrix)
conf_list <- GetConfList(network)
head(conf_list)