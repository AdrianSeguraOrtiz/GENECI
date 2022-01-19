if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

BiocManager::install("grndata")

library(grndata)

l.data <- getData(datasource.name="syntren300")

mtx.exp <- t(l.data[[1]])

mtx.gs <- l.data[[2]]