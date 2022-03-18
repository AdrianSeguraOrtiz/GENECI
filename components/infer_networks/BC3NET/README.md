## NAME

BC3NET

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the BC3NET technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_networks/bc3net -f components/infer_networks/BC3NET/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/infer_networks/bc3net expression_data.csv
```
