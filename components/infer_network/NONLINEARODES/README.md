## NAME

NONLINEARODES

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the NONLINEARODES technique.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_infer-network_nonlinearodes -f components/infer_network/NONLINEARODES/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_nonlinearodes expression_data.csv inferred_networks
```
