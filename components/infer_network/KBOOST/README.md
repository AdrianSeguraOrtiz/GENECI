## NAME

KBOOST

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the KBOOST technique.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_infer-network_kboost:1.0.0 -f components/infer_network/KBOOST/Dockerfile .
=======
docker build -t adriansegura99/geneci_infer-network_kboost:2.5.1 -f components/infer_network/KBOOST/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_kboost expression_data.csv inferred_networks
```
