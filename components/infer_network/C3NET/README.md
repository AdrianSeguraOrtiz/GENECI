## NAME

C3NET

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the C3NET technique.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_infer-network_c3net:1.0.0 -f components/infer_network/C3NET/Dockerfile .
=======
docker build -t adriansegura99/geneci_infer-network_c3net:2.5.1 -f components/infer_network/C3NET/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_c3net expression_data.csv inferred_networks
```
