## NAME

DREAM4

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading evaluation data from DREAM4 challenge.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_extract-data_dream4-eval:1.0.0 -f components/extract_data/DREAM4/EVAL/Dockerfile .
```

## Run

```
docker run -v $(pwd)/input_data:/usr/local/src/input_data/ adriansegura99/geneci_extract-data_dream4-eval --output-folder input_data --username TFM-SynapseAccount --password TFM-SynapsePassword
```
