# Read the data code in the folder
get_data_f <- function(path) {
  # Read all files in the same directory
  fileNames <- dir(path)
  filePath <- sapply(fileNames, function(x) {
    paste(path, x, sep = "/")
  })
  data <- lapply(filePath, function(x) {
    read.table(x, header = FALSE, sep = "")
  })
  return(data)
}
get_data_t <- function(path) {
  fileNames <- dir(path)
  filePath <- sapply(fileNames, function(x) {
    paste(path, x, sep = "/")
  })
  data <- lapply(filePath, function(x) {
    read.table(x, header = TRUE, sep = "")
  })
  return(data)
}
get_data_tab <- function(path) {
  fileNames <- dir(path)
  filePath <- sapply(fileNames, function(x) {
    paste(path, x, sep = "/")
  })
  data <- lapply(filePath, function(x) {
    read.table(x, header = TRUE, sep = "\t")
  })
  return(data)
}
## output file
put_data <- function(outPath, res, filename1) {
  write.table(res, file = outPath, append = T, sep = ",", quote = F, row.names = F, col.names = F)
}

shrink <- function(mydata, lisan) {
  mydata <- infotheo::discretize(mydata, "equalwidth", lisan)
  col <- ncol(mydata)
  row <- nrow(mydata)

  MI_J <- matrix(0, nr = col, nc = col)
  # Calculate the frequency by the column, because the column represents the gene
  for (m in 2:col) {
    for (n in 1:m) {
      b <- mydata[, c(n, m)]
      b[, 3] <- 1
      d <- aggregate(b[, 3], by = list(v1 = b[, 1], v2 = b[, 2]), FUN = "sum")
      colnames(d) <- c("v1", "v2", "v3")
      f <- spread(d, key = "v1", value = "v3", fill = 0)
      rownames(f) <- f[, 1] # Take the first column of the data box as the row name
      f <- f[, -1]
      freq <- as.matrix(f)
      MI_J[m, n] <- entropy::mi.shrink(freq, verbose = FALSE)
      MI_J[n, m] <- MI_J[m, n]
    }
  }

  res <- minet::clr(MI_J, skipDiagonal = 1)
  for (m in 2:col) {
    for (n in 1:m) {
      if (res[m, n] == "NaN") {
        res[m, n] <- 0
        res[n, m] <- 0
      }
    }
  }
  res <- res / max(res)
  colnames(res) <- colnames(mydata)
  rownames(res) <- colnames(mydata)
  return(res)
}


matrix.list <- function(res) {
  ## Adjacency matrix transforms adjacency list and sorts
  result <- res
  b <- data.frame(v1 = 1:nrow(result)^2, v2 = 1:nrow(result)^2, value = 1:nrow(result)^2)
  for (i in 1:nrow(result)) {
    for (j in 1:ncol(result)) {
      ## Replace the possible default value NaN
      if (result[i, j] == "NaN") {
        result[i, j] <- 0
      }
      a <- c(row.names(result)[i], colnames(result)[j], result[i, j])
      b[(i - 1) * nrow(result) + j, ] <- a
    }
  }
  ## Sort by value
  or <- order(b[, 3], decreasing = T)
  b <- b[or, ]
  return(b)
}

## Adjacency list to matrix
list_to_matrix <- function(mydata, list) {
  AMN <- matrix(0, nrow = ncol(mydata), ncol = ncol(mydata))
  colnames(AMN) <- colnames(mydata)
  row.names(AMN) <- colnames(mydata)
  list[, 1:2] <- apply(list[, 1:2], 2, as.character)
  colnames(list) <- c("V1", "V2", "V3")
  for (i in 1:nrow(list)) {
    AMN[list$V1[i], list$V2[i]] <- list$V3[i]
  }
  return(AMN)
}

## design conditions
canshu <- function(mydata, net1, my_prediction_end1) {
  colnames(net1) <- c("V1", "V2", "V3")
  my_prediction_end <- my_prediction_end1[my_prediction_end1[, 3] > 0, 1:2]
  true <- net1[net1$V3 == 1, 1:2]
  options(max.print = 1000000)

  all_possible <- as.data.frame(net1[, 1:2])
  false <- sqldf("SELECT * FROM [all_possible] EXCEPT SELECT * FROM [true]")
  false1 <- sqldf("SELECT * FROM [all_possible] EXCEPT SELECT * FROM [my_prediction_end]")
  tp <- sqldf("SELECT * FROM [true] InterSect SELECT * FROM [my_prediction_end]")
  fp <- sqldf("SELECT * FROM [false] InterSect SELECT * FROM [my_prediction_end]")
  tn <- sqldf("SELECT * FROM [false] InterSect SELECT * FROM [false1]")
  fn <- sqldf("SELECT * FROM [true] InterSect SELECT * FROM [false1]")
  PPV <- nrow(tp) / (nrow(tp) + nrow(fp))
  TPR <- nrow(tp) / (nrow(tp) + nrow(fn))
  afsbn_F <- 2 * PPV * TPR / (PPV + TPR)
  ACC <- (nrow(tp) + nrow(tn)) / (nrow(tp) + nrow(tn) + nrow(fp) + nrow(fn))
  MCC <- (nrow(tp) * nrow(tn) - nrow(fp) * nrow(fn)) / (sqrt((nrow(tp) + nrow(fp))) * sqrt((nrow(tp) + nrow(fn))) * sqrt((nrow(tn) + nrow(fp))) * sqrt((nrow(tn) + nrow(fn))))
  FPR <- nrow(fp) / (nrow(fp) + nrow(tn))
  colnames(net1) <- c("v1", "v2", "label")
  colnames(my_prediction_end1) <- c("v1", "v2", "value")
  my <- full_join(net1, my_prediction_end1, by = c("v1", "v2"))
  my[is.na(my)] <- 0
  AUPR <- AUC(obs = my$label, pred = my$value, curve = "PR", simplif = T, main = "PR curve")
  AUROC <- AUC(obs = my$label, pred = my$value, curve = "ROC", simplif = T, main = "ROC curve")

  r <- array(data = NA, dim = c(1, 12))
  colnames(r) <- c("tp", "fp", "tn", "fn", "TPR", "PPV", "afsbn_F", "FPR", "ACC", "MCC", "AUPR", "AUROC")
  r[1, 1] <- nrow(tp)
  r[1, 2] <- nrow(fp)
  r[1, 3] <- nrow(tn)
  r[1, 4] <- nrow(fn)
  r[1, 5] <- TPR
  r[1, 6] <- PPV
  r[1, 7] <- afsbn_F
  r[1, 8] <- FPR
  r[1, 9] <- ACC
  r[1, 10] <- MCC
  r[1, 11] <- AUPR
  r[1, 12] <- AUROC
  return(r)
}
## Record the elapsed time
f <- function(start_time) {
  start_time <- as.POSIXct(start_time)
  dt <- difftime(Sys.time(), start_time, units = "secs")
  # Since you only want the H:M:S, we can ignore the date...
  # but you have to be careful about time-zone issues
  format(.POSIXct(dt, tz = "GMT"), "%H:%M:%S")
}
