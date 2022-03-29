## NAME

MRNETB

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the MRNETB technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_network/mrnetb -f components/infer_network/MRNETB/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ eagrn-inference/infer_network/mrnetb expression_data.csv inferred_networks
```
