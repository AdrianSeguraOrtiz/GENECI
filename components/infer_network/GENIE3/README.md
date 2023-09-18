## NAME

GENIE3

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the GENIE3 technique. Several configurations are possible as a result of the three available regressors: Random Forest regression (RF), Gradient Boosting Machine regression with early-stopping regularization (GBM) or ExtraTrees regression (ET).

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_infer-network_genie3:1.0.0 -f components/infer_network/GENIE3/Dockerfile .
=======
docker build -t adriansegura99/geneci_infer-network_genie3:2.0.0 -f components/infer_network/GENIE3/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_genie3 expression_data.csv inferred_networks RF
```
