## NAME

DREAM4

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading differential expression data and gold standards from DREAM4 challenge.

# DOCKER

## Build

```
docker build -t eagrn-inference/extract_data/dream4/expgs -f components/extract_data/DREAM4/EXPGS/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/extract_data/dream4/expgs ExpressionData expression_data
```
