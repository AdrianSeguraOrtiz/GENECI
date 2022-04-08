## NAME

JUMP3

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the JUMP3 technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_network/jump3 -f components/infer_network/JUMP3/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ eagrn-inference/infer_network/jump3 expression_data.csv inferred_networks
```
