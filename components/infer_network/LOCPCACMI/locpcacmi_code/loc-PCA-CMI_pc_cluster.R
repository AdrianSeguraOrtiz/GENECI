library(readr)
library(R.matlab)
library(Matrix)
library(RLowPC)
library(reshape2)
library(fdrtool)
library(gtools)

ARGS <- commandArgs(trailingOnly = TRUE)
datafile <- ARGS[1]

data.exp <- t(read.table(datafile, sep=",", head=T, row.names=1))
genes <- colnames(data.exp)

inf.zeroPC <- zeroPC(data.exp = data.exp, method = "pearson")

topN <- ceiling(0.2 * (length(genes) * (length(genes) - 1) / 2))

inf.edge <- inf.zeroPC[1:topN, 1:3]

inf.zeropc.adj <- edgelist2adjmatrix(inf.edge, genes = genes, directed = F)
for (i in 1:dim(inf.zeropc.adj)[1]) {
    idx <- which(inf.zeropc.adj[i, ] > 0)
    mixOrderCluster <- mixedsort(colnames(inf.zeropc.adj)[c(i, idx)])
    cat(paste(i, "th/#", length(mixOrderCluster), sep = ""), ":[", mixOrderCluster, "]\n")
}

writeMat("tmp/.X11-unix/tmp.mat", adj = inf.zeropc.adj)
