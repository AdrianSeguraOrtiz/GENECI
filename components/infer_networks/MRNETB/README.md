## NAME

MRNETB

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the MRNETB technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_networks/mrnetb -f components/infer_networks/MRNETB/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/infer_networks/mrnetb expression_data.csv
```
