## NAME

Extract Data

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading differential expression data from various databases such as DREAM4, SynTReN, Rogers and GeneNetWeaver.

# DOCKER

## Build

```
docker build -t eagrn-inference/extract_data -f components/extract_data/Dockerfile .
```

## Run

```
docker run -v $(pwd)/expression_data:/usr/local/src/expression_data/ eagrn-inference/extract_data DREAM4 extract_data
```
