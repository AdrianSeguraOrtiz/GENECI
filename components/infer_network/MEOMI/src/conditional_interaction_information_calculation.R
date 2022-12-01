CMI2 <- function(temp, data, lamda, order0) {
  n_gene <- nrow(data)
  G <- matrix(1, nrow = n_gene, ncol = n_gene)
  G[upper.tri(G, diag = TRUE)] <- 0
  G <- G + t(G)
  Gval <- G
  order <- -1
  t <- 0

  while (t == 0) {
    order <- order + 1
    if (order0 != 0) {
      if (order > order0) {
        break
      }
    }

    res <- edgereduce1(G, Gval, order, data, t, lamda, temp)
    G <- res$G
    Gval <- res$Gval
    t <- res$t
    if (t == 0) {
      print("No edge is reduce! Algorithm  finished!")
      break
    } else {
      t <- 0
    }
  }
  order <- order - 1
  res1 <- list(G = G, Gval = Gval, order = order)
  return(res1)
}

edgereduce1 <- function(G, Gval, order, data, t, lamda, temp) {
  val <- temp
  G0 <- G
  if (order == 0) {
    write.table(G, file = "G0.csv", append = F, sep = ",", quote = F, row.names = F, col.names = F)
    write.table(Gval, file = "Gval0.csv", append = F, sep = ",", quote = F, row.names = F, col.names = F)
    write.table(val, file = "val0.csv", append = F, sep = ",", quote = F, row.names = F, col.names = F)
    G <- read.table("G0.csv", header = F, sep = ",")
    Gval <- read.table("Gval0.csv", header = F, sep = ",")
    val <- read.table("val0.csv", header = F, sep = ",")
    for (ii in 2:nrow(G)) {
      for (jj in 1:ii) {
        if (G[ii, jj] != 0) {
          cmiv <- val[ii, jj]
          Gval[ii, jj] <- cmiv
          Gval[jj, ii] <- cmiv
          if (cmiv < lamda) {
            G[ii, jj] <- 0
            G[jj, ii] <- 0
          }
        }
      }
    }
    t <- t + 1
  } else {
    for (i in 2:nrow(G)) {
      for (j in 1:i) {
        if (G[i, j] != 0) {
          adj <- NULL
          for (k in 1:nrow(G)) {
            if (G[i, k] == 1 && G[j, k] == 1) {
              adj <- cbind(adj, k)
            }
          }

          if (!is.null(adj)) {
            if (ncol(adj) >= order) {
              ## List all cases where transpose is required
              adj <- as.data.frame(adj)
              combntnslist <- t(combn(adj, order))
              combntnsrow <- nrow(combntnslist)
              cmiv <- 0
              v1 <- data[i, ]
              v2 <- data[j, ]
              for (k in 1:combntnsrow) {
                vcs <- data[as.numeric(combntnslist[k, ]), ]
                a <- MI2(v1, v2, vcs)
                cmiv <- max(cmiv, a)
              }
              Gval[i, j] <- cmiv
              Gval[j, i] <- cmiv
              if (cmiv < (lamda * combntnsrow)) {
                G[i, j] <- 0
                G[j, i] <- 0
              }
              t <- t + 1
            }
          }
        }
      }
    }
  }
  res <- list(G = G, Gval = Gval, t = t)
  return(res)
}

cmi <- function(v1, v2, vcs) {
  if (missing(vcs)) {
    c1 <- det(cov(t(v1)))
    c2 <- det(cov(t(v2)))
    c3 <- det(cov(t(rbind(v1, v2))))
    cmiv <- 0.5 * log(c1 * c2 / c3)
  } else {
    c1 <- det(cov(t(rbind(v1, vcs))))
    c2 <- det(cov(t(rbind(v2, vcs))))
    c3 <- det(cov(t(vcs)))
    c4 <- det(cov(t(rbind(v1, v2, vcs))))
    cmiv <- 0.5 * log((c1 * c2) / (c3 * c4))
  }
  if (is.infinite(cmiv)) {
    cmiv <- 1.0e+010
  }
  return(cmiv)
}

MI2 <- function(x, y, z) {
  r_dmi <- (cas(x, y, z) + cas(y, x, z)) / 2

  return(r_dmi)
}

cas <- function(x, y, z) {
  n1 <- nrow(z)
  n <- n1 + 2
  Cov <- cov(t(x))
  Covm <- cov(t(rbind(x, y, z)))
  Covm1 <- cov(t(rbind(x, z)))

  InvCov <- solve(Cov)
  InvCovm <- solve(Covm)
  InvCovm1 <- solve(Covm1)

  C11 <- InvCovm1[1, 1]
  C12 <- 0
  C13 <- InvCovm1[1, 2:(1 + n1)]
  C23 <- InvCovm[2, 3:(2 + n1)] - InvCovm[1, 2] * (1 / (InvCovm[1, 1] - InvCovm1[1, 1] + InvCov[1, 1])) * (InvCovm[1, 3:(2 + n1)] - InvCovm1[1, 2:(1 + n1)])
  C22 <- InvCovm[2, 2] - InvCovm[1, 2]^2 * (1 / (InvCovm[1, 1] - InvCovm1[1, 1] + InvCov[1, 1]))
  C112233 <- as.matrix(InvCovm[1, 3:(2 + n1)] - InvCovm1[1, 2:(1 + n1)]) %*% t(as.matrix(InvCovm[1, 3:(2 + n1)] - InvCovm1[1, 2:(1 + n1)]))
  C2233 <- (1 / (InvCovm[1, 1] - InvCovm1[1, 1] + InvCov[1, 1])) * C112233
  C33 <- InvCovm[3:(2 + n1), 3:(2 + n1)] - C2233
  InvC <- rbind(cbind(C11, C12, t(as.matrix(C13))), cbind(C12, C22, t(as.matrix(C23))), cbind((as.matrix(C13)), as.matrix(C23), C33))
  C0 <- Cov[1, 1] * (InvCovm[1, 1] - InvCovm1[1, 1] + InvCov[1, 1])
  CS <- 0.5 * (sum(diag(InvC %*% Covm)) + log(C0) - n)
  return(CS)
}
