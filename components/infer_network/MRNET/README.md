## NAME

MRNET

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the MRNET technique.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_infer-network_mrnet -f components/infer_network/MRNET/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_mrnet expression_data.csv inferred_networks
```
