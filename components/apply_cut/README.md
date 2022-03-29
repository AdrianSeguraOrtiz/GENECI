## NAME

Extract Data

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading differential expression data from various databases such as DREAM4, SynTReN, Rogers and GeneNetWeaver.

# DOCKER

## Build

```
docker build -t eagrn-inference/apply_cut -f components/apply_cut/Dockerfile .
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ eagrn-inference/apply_cut inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv inferred_networks/dream4_010_01_exp/gene_names.txt inferred_networks/dream4_010_01_exp/networks/GRN_ARACNE.csv MinConfidence 0.1
```
