## NAME

GRNDATA

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading time series of gene expression data and gold standards from several databases such as SynTReN, Rogers and GeneNetWeaver.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_extract-data_grndata:1.0.0 -f components/extract_data/GRNDATA/Dockerfile .
=======
docker build -t adriansegura99/geneci_extract-data_grndata:2.0.0 -f components/extract_data/GRNDATA/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/input_data:/usr/local/src/input_data/ adriansegura99/geneci_extract-data_grndata SynTReN ExpressionData input_data
```
