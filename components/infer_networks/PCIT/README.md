## NAME

PCIT

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the PCIT technique.

# DOCKER

## Build

```
docker build -t eagrn-inference/infer_networks/pcit -f components/infer_networks/PCIT/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/infer_networks/pcit expression_data.csv
```
