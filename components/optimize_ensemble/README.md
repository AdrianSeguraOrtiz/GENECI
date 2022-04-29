## NAME

Extract Data

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for downloading differential expression data from various databases such as DREAM4, SynTReN, Rogers and GeneNetWeaver.

# DOCKER

## Build

```
docker build -t eagrn-inference/optimize_ensemble -f components/optimize_ensemble/Dockerfile .
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ eagrn-inference/optimize_ensemble /mnt/volumen/adriansegura/TFM/EAGRN-Inference/inferred_networks/dream4_010_01_exp/ SBXCrossover PolynomialMutation GreedyRepair 100 10000 MinConfFreq 0.2 0.75 0.25 8
```
