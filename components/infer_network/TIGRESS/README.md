## NAME

TIGRESS

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the TIGRESS technique.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_infer-network_tigress:1.0.0 -f components/infer_network/TIGRESS/Dockerfile .
=======
docker build -t adriansegura99/geneci_infer-network_tigress:3.0.0 -f components/infer_network/TIGRESS/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_tigress expression_data.csv inferred_networks
```
