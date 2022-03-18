## NAME

CLR

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the CLR technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_networks/clr -f components/infer_networks/CLR/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/infer_networks/clr expression_data.csv
```
