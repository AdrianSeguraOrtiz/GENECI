################# MEOMI#################
MEOMI <- function(mydata, bins, lamda, order) {
  res1 <- minet(mydata, method = "clr", estimator = "mi.shrink", disc = "equalwidth", nbins = bins)
  res2 <- shrink(mydata, bins)
  b1 <- matrix.list(res1)
  b2 <- matrix.list(res2)
  # Replace the default value NaN
  for (j in 1:nrow(b1)) {
    if (b1[j, ]$value == "NaN") {
      b1[j, ]$value <- 0
    }
  }
  for (k in 1:nrow(b2)) {
    if (b2[k, ]$value == "NaN") {
      b2[k, ]$value <- 0
    }
  }
  my_prediction1 <- b1[b1[, 3] > 0, ]
  my_prediction2 <- b2[b2[, 3] > 0, ]
  my_prediction_end <- full_join(my_prediction1, my_prediction2, by = c("v1", "v2"))
  my_prediction_end[is.na(my_prediction_end)] <- 0
  my_prediction_end$v3 <- rowSums(as.data.frame(lapply(my_prediction_end[, 3:4], as.numeric)))
  my_prediction_end$v3 <- my_prediction_end$v3 / max(my_prediction_end$v3)
  for (mm in 1:nrow(my_prediction_end)) {
    if (my_prediction_end[mm, 3] != 0 & my_prediction_end[mm, 4] != 0) {
      my_prediction_end[mm, 5] <- max(my_prediction_end[mm, 3], my_prediction_end[mm, 4])
    }
  }

  my_prediction_end1 <- my_prediction_end[, c(1, 2, 5)]
  temp <- list_to_matrix(mydata, my_prediction_end1)
  original_data_new <- t(mydata)
  original_data_new <- as.data.frame(original_data_new)
  res_new <- CMI2(temp, original_data_new, lamda, order)
  colnames(res_new$Gval) <- colnames(temp)
  row.names(res_new$Gval) <- row.names(temp)
  Gval <- NULL
  for (ii in 1:nrow(res_new$G)) {
    for (jj in 1:ncol(res_new$G)) {
      if (ii != jj) {
        if (res_new$G[ii, jj] == 1) {
          Gval <- rbind(c(row.names(res_new$Gval)[ii], colnames(res_new$Gval)[jj], res_new$Gval[ii, jj]), Gval)
        }
      }
    }
  }
  Gval <- as.data.frame(Gval)
  or <- order(Gval[, 3], decreasing = T)
  Gval <- Gval[or, ]
  colnames(Gval) <- c("v1", "v2", "value")
  Gval[, 3] <- as.data.frame(as.numeric(Gval$value) / max(as.numeric(Gval$value)))
  return(Gval)
}
