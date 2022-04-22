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
docker run -v $(pwd)/input_data:/usr/local/src/input_data/ eagrn-inference/extract_data/dream4/eval --output-folder input_data --username TFM-SynapseAccount --password TFM-SynapsePassword
```