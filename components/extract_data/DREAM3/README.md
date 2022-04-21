## NAME

DREAM3

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading differential expression data, gold standards and evaluation data from DREAM3 challenge.

# DOCKER

## Build

```
docker build -t eagrn-inference/extract_data/dream3 -f components/extract_data/DREAM3/Dockerfile .
```

## Run

```
docker run -v $(pwd)/input_data:/usr/local/src/input_data/ eagrn-inference/extract_data/dream3 --category ExpressionData --output-folder input_data --username TFM-SynapseAccount --password TFM-SynapsePassword
```
