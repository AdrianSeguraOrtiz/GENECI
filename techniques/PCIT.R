ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) >= 2) { 
    cat("ARGS == 1: the argument will be treated as input csv file \n")
    in_file <- ARGS[1]
    cat("ARGS == 2: the argument will be treated as output identifier string \n")
    out_id <- ARGS[2]
} else if (length(ARGS) == 1 && ARGS[1] == "--help") {
    cat("Usage: \n")
    cat("Rscript PCIT.R input.csv out_id \n") 
    cat("Arguments required: \n")
    cat("\t 1) CSV input file \n")
    cat("\t 2) Output identifier string \n")
    stop("", call. = FALSE)
} else if (length(ARGS) < 2) {
  stop("More arguments required, write --help to see the options \n", call. = FALSE)
}

# Install BiocManager if not already installed
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install CeTF
#BiocManager::install("CeTF")

# Load CeTF
suppressMessages(library(CeTF))

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

# Delete all rows with confidence 0
conf_list <- conf_list[conf_list[,3] != 0, ]

# Save list
write.table(conf_list, paste0(out_id, ".csv"), sep=",", col.names=F, row.names=F, quote=F)

