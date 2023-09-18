ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) { 
    cat("ARGS == 1: the argument will be treated as csv file with the inferred network \n")
    inferred_file <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as csv file with the gold standard \n")
    gs_file <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript evaluate.R final_network.csv gold_standard.csv \n") 
    cat("Arguments required: \n")
    cat("\t 1) CSV file with the inferred network \n")
    cat("\t 2) CSV file with the gold standard \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 2) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

lbs <- c("PRROC", "parallel")
not_installed <- lbs[!(lbs %in% installed.packages()[ , "Package"])]
if(length(not_installed)) install.packages(not_installed, repos = "http://cran.us.r-project.org")
sapply(lbs, require, character.only=TRUE)

suppressMessages(library(PRROC))
suppressMessages(library(parallel))

inferred_network <- read.table(inferred_file, sep=",", head=T, row.names=1)
gs_network <- read.table(gs_file, sep=",", head=T, row.names=1)

v.inferred <- unlist(mcmapply(1:nrow(inferred_network), FUN = function(row) {
    mcmapply(1:row, FUN = function(col) {
        return(inferred_network[row, col])
    })
}))

v.gs <- unlist(mcmapply(1:nrow(gs_network), FUN = function(row) {
    mcmapply(1:row, FUN = function(col) {
        return(gs_network[row, col])
    })
}))

fg <- v.inferred[v.gs == 1]
bg <- v.inferred[v.gs == 0]

# ROC Curve    
roc <- roc.curve(scores.class0 = fg, scores.class1 = bg)
print(paste("AUROC:", roc$auc))

# PR Curve
pr <- pr.curve(scores.class0 = fg, scores.class1 = bg)
print(paste("AUPR:", pr$auc.integral))