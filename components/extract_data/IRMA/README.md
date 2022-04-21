## NAME

IRMA

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading differential expression data and gold standards from IRMA dataset.

# DOCKER

## Build

```
docker build -t eagrn-inference/extract_data/irma -f components/extract_data/IRMA/Dockerfile .
```

## Run

```
docker run -v $(pwd)/input_data:/usr/local/src/input_data/ eagrn-inference/extract_data/irma ExpressionData input_data
```
