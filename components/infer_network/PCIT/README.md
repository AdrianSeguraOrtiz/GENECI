## NAME

PCIT

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

Given a CSV file with differential expression data, this component infers its gene regulatory network by applying the PCIT technique.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_infer-network_pcit:1.0.0 -f components/infer_network/PCIT/Dockerfile .
```

## Run

```
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ adriansegura99/geneci_infer-network_pcit expression_data.csv inferred_networks
```
