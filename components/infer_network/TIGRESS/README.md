## NAME

TIGRESS

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the TIGRESS technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_network/tigress -f components/infer_network/TIGRESS/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ eagrn-inference/infer_network/tigress expression_data.csv inferred_networks
```
