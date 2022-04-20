## NAME

DREAM4

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading evaluation data from DREAM4 challenge.

# DOCKER

## Build

```
docker build -t eagrn-inference/extract_data/dream4/eval -f components/extract_data/DREAM4/EVAL/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/extract_data/dream4/eval --output-folder expression_data --username TFM-SynapseAccount --password TFM-SynapsePassword
```
