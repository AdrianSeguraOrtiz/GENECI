## NAME

LEAP

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the LEAP technique.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_infer-network_leap:2.5.1 -f components/infer_network/LEAP/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_leap expression_data.csv inferred_networks
```
