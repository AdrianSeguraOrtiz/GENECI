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
docker run -v $(pwd)/inferred_networks:/usr/local/src/inferred_networks/ eagrn-inference/apply_cut inferred_networks/dream4_010_01_exp/lists/GRN_ARACNE.csv MinConfidence 0.5
```
