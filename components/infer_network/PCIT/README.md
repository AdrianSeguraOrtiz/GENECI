## NAME

PCIT

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with time series of gene expression data, this component infers its gene regulatory network by applying the PCIT technique.

# DOCKER

## Build

```
<<<<<<< HEAD
docker build -t adriansegura99/geneci_infer-network_pcit:1.0.0 -f components/infer_network/PCIT/Dockerfile .
=======
docker build -t adriansegura99/geneci_infer-network_pcit:3.0.0 -f components/infer_network/PCIT/Dockerfile .
>>>>>>> dev
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_pcit expression_data.csv inferred_networks
```
