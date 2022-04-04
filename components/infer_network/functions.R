# Install gdata if not already installed
if(! "gdata" %in% installed.packages()[,"Package"]) install.packages("gdata")

# Load gdata
suppressMessages(library(gdata))

# Get confidence list from network
GetConfList <- function(network) {
    df = data.frame(as.table(network))
    conf_list <- df[order(df$Freq, decreasing=TRUE), ]
    return(conf_list)
}

# Rescale trust levels between 0 and 1 and remove links with no network presence
ProcessList <- function(conf_list) {
    v.conf <- conf_list[,3]
    v.scaled <- (v.conf - min(v.conf)) / (max(v.conf) - min(v.conf))
    conf_list[,3] <- v.scaled
    conf_list <- conf_list[conf_list[,3] != 0, ]
    return(conf_list)
}