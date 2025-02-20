## NAME

CLR

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the CLR technique.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_infer-network_clr:4.0.0 -f components/infer_network/CLR/Dockerfile .
=======
docker build -t adriansegura99/geneci_infer-network_clr:4.0.0 -f components/infer_network/CLR/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_clr expression_data.csv inferred_networks
```
