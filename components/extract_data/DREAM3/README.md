## NAME

DREAM3

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading time series of gene expression data, gold standards and evaluation data from DREAM3 challenge.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_extract-data_dream3:4.0.0 -f components/extract_data/DREAM3/Dockerfile .
=======
docker build -t adriansegura99/geneci_extract-data_dream3:4.0.0 -f components/extract_data/DREAM3/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/input_data:/usr/local/src/input_data/ adriansegura99/geneci_extract-data_dream3 --category ExpressionData --output-folder input_data --username TFM-SynapseAccount --password TFM-SynapsePassword
```
