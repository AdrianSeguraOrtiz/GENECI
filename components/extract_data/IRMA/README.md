## NAME

IRMA

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading time series of gene expression data and gold standards from IRMA dataset.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_extract-data_irma:4.0.0 -f components/extract_data/IRMA/Dockerfile .
=======
docker build -t adriansegura99/geneci_extract-data_irma:4.0.0 -f components/extract_data/IRMA/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/input_data:/usr/local/src/input_data/ adriansegura99/geneci_extract-data_irma ExpressionData input_data
```
