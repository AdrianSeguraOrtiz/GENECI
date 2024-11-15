## NAME

DREAM4

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading time series of gene expression data and gold standards from DREAM4 challenge.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_extract-data_dream4-expgs:1.0.0 -f components/extract_data/DREAM4/EXPGS/Dockerfile .
=======
docker build -t adriansegura99/geneci_extract-data_dream4-expgs:2.5.1 -f components/extract_data/DREAM4/EXPGS/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/input_data:/usr/local/src/input_data/ adriansegura99/geneci_extract-data_dream4-expgs ExpressionData input_data
```
