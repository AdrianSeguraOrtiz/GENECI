## NAME

GENIE3

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the GENIE3 technique. Several configurations are possible as a result of the three available regressors: Random Forest regression (RF), Gradient Boosting Machine regression with early-stopping regularization (GBM) or ExtraTrees regression (ET).

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_network/genie3 -f components/infer_network/GENIE3/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ eagrn-inference/infer_network/genie3 expression_data.csv inferred_networks RF
```
