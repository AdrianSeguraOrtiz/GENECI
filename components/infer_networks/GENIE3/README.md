## NAME

GENIE3

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the GENIE3 technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_networks/genie3 -f components/infer_networks/GENIE3/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/infer_networks/genie3 expression_data.csv
```
