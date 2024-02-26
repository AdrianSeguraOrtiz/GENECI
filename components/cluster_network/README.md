## NAME

Cluster Network

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for dividing an initial gene network into various communities following the Infomap (recommended) or Louvain grouping algorithm

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_cluster-network:3.0.0 -f components/cluster_network/Dockerfile .
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ adriansegura99/geneci_cluster-network:3.0.0 --confidence-list inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv --output-folder tmp
```
