## NAME

CLR

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the CLR technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_network/clr -f components/infer_network/CLR/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ eagrn-inference/infer_network/clr expression_data.csv inferred_networks
```
