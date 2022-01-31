# Install gdata if not already installed
if(! "gdata" %in% installed.packages()[,"Package"]) install.packages("gdata")

# Load gdata
library(gdata)

# Get confidence list from network
GetConfList <- function(network) {
    lowerTriangle(network) <- 0
    df = data.frame(as.table(network))
    conf_list <- df[order(df$Freq, decreasing=TRUE), ]
    return(conf_list)
}