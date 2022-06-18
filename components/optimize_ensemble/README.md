## NAME

Optimize Ensemble

## AUTHOR

Adrián Segura Ortiz

## DESCRIPTION

This component is responsible for reading different trust lists and creating an optimal consensus network from them by applying an evolutionary algorithm.

# DOCKER

## Build

```
docker build -t adriansegura99/geneci_optimize-ensemble -f components/optimize_ensemble/Dockerfile .
```

## Run

```
docker run -v $(pwd)/tmp:/usr/local/src/tmp/ adriansegura99/geneci_optimize-ensemble /mnt/volumen/adriansegura/TFM/GENECI/inferred_networks/dream4_010_01_exp/ SBXCrossover PolynomialMutation GreedyRepair 100 10000 MinConfFreq 0.2 0.75 0.25 AsyncParallel 8
```
