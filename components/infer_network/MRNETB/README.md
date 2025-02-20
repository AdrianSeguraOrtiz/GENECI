## NAME

MRNETB

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the MRNETB technique.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_infer-network_mrnetb:4.0.0 -f components/infer_network/MRNETB/Dockerfile .
=======
docker build -t adriansegura99/geneci_infer-network_mrnetb:4.0.0 -f components/infer_network/MRNETB/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_mrnetb expression_data.csv inferred_networks
```
