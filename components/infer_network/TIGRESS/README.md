## NAME

TIGRESS

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the TIGRESS technique.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_infer-network_tigress:1.0.0 -f components/infer_network/TIGRESS/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_tigress expression_data.csv inferred_networks
```
