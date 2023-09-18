## NAME

PIDC

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the PIDC technique.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_infer-network_pidc:2.0.0 -f components/infer_network/PIDC/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_pidc expression_data.csv inferred_networks
```
