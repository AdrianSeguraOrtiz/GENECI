## NAME

ARACNE

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the ARACNE technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_networks/aracne .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/infer_networks/aracne expression_data.csv
```
