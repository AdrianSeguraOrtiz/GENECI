## NAME

DREAM5

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading differential expression data, gold standards and evaluation data from DREAM5 challenge.

# DOCKER

## Build

```
docker build -t eagrn-inference/extract_data/dream5 -f components/extract_data/DREAM5/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/extract_data/dream5 --category ExpressionData --output-folder expression_data --username TFM-SynapseAccount --password TFM-SynapsePassword
```
