## NAME

MRNET

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the MRNET technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_networks/mrnet -f components/infer_networks/MRNET/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/infer_networks/mrnet expression_data.csv
```
