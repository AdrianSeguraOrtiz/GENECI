## NAME

KBOOST

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the KBOOST technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_network/kboost -f components/infer_network/KBOOST/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ eagrn-inference/infer_network/kboost expression_data.csv inferred_networks
```
